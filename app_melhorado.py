import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from PIL import Image as PilImage
import io
import base64
import pandas as pd
import json
import os

# ================= CONFIGURAÇÕES =================

DB_NAME = "vistoria.db"

st.set_page_config(
    page_title="Vistoria Imóveis Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CONFIGS DE IMÓVEIS =================
# Define os cômodos disponíveis para cada tipo de imóvel.
# Chave: nome interno, Valor: label exibida no plural

TIPOS_COMERCIAIS = [
    "Sala Comercial",
    "Ponto Comercial",
    "Loja",
    "Galpão",
    "Escritório",
    "Consultório",
    "Restaurante/Bar",
    "Clínica/Laboratório",
    "Outro Comercial",
]

CONFIGS_COMODOS = {
    # ---- RESIDENCIAL ----
    "Residencial": {
        "icone": "🏠",
        "comodos": {
            "quartos":       "Quartos",
            "banheiros":     "Banheiros",
            "salas":         "Salas",
            "cozinhas":      "Cozinhas",
            "areas_servico": "Áreas de Serviço",
            "vagas_garagem": "Vagas de Garagem",
        },
    },

    # ---- COMERCIAIS ----
    "Sala Comercial": {
        "icone": "🏢",
        "comodos": {
            "recepcao":      "Recepções",
            "sala_reuniao":  "Salas de Reunião",
            "escritorio":    "Escritórios/Estações",
            "banheiro":      "Banheiros",
            "copa":          "Copas",
            "deposito":      "Depósitos",
        },
    },

    "Ponto Comercial": {
        "icone": "🏪",
        "comodos": {
            "salao":     "Salões Principais",
            "copa":      "Copas",
            "banheiro":  "Banheiros",
            "deposito":  "Depósitos",
        },
    },

    "Loja": {
        "icone": "🛍️",
        "comodos": {
            "salao_vendas": "Salões de Vendas",
            "provador":     "Provadores",
            "banheiro":     "Banheiros",
            "copa":         "Copas",
            "deposito":     "Depósitos/Estoque",
        },
    },

    "Galpão": {
        "icone": "🏭",
        "comodos": {
            "area_producao": "Áreas de Produção/Industrial",
            "escritorio":    "Escritórios",
            "banheiro":      "Banheiros",
            "refeitorio":    "Refeitórios",
            "deposito":      "Depósitos",
            "doca":          "Docas/Carregamento",
        },
    },

    "Escritório": {
        "icone": "💼",
        "comodos": {
            "sala_trabalho": "Salas de Trabalho",
            "sala_reuniao":  "Salas de Reunião",
            "recepcao":      "Recepções",
            "banheiro":      "Banheiros",
            "copa":          "Copas",
        },
    },

    "Consultório": {
        "icone": "🩺",
        "comodos": {
            "sala_espera":  "Salas de Espera",
            "consultorio":  "Consultórios",
            "recepcao":     "Recepções",
            "banheiro":     "Banheiros",
            "copa":         "Copas",
        },
    },

    "Restaurante/Bar": {
        "icone": "🍽️",
        "comodos": {
            "salao_atendimento": "Salões de Atendimento",
            "cozinha":           "Cozinhas",
            "banheiro":          "Banheiros",
            "deposito":          "Depósitos/Despensas",
            "area_externa":      "Áreas Externas",
        },
    },

    "Clínica/Laboratório": {
        "icone": "🏥",
        "comodos": {
            "sala_espera":   "Salas de Espera",
            "sala_atend":    "Salas de Atendimento",
            "laboratorio":   "Laboratórios/Exames",
            "recepcao":      "Recepções",
            "banheiro":      "Banheiros",
            "copa":          "Copas",
            "deposito":      "Depósitos/Almoxarifado",
        },
    },

    "Outro Comercial": {
        "icone": "🏗️",
        "comodos": {
            "ambiente":  "Ambientes Principais",
            "banheiro":  "Banheiros",
            "copa":      "Copas",
            "deposito":  "Depósitos",
            "outro":     "Outros Ambientes",
        },
    },
}

# CSS Customizado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    :root {
        --primary-color: #1a2b4a;
        --secondary-color: #C9A961;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --border-color: #e2e8f0;
        --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Poppins', sans-serif !important; font-weight: 600 !important; color: #1a2b4a !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: white; border-radius: 12px; padding: 0.5rem; box-shadow: var(--shadow); }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 8px; padding: 0 24px; font-weight: 500; background-color: transparent; border: none; color: #64748b; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important; color: white !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stTextArea > div > div > textarea { border-radius: 8px !important; border: 2px solid var(--border-color) !important; padding: 0.75rem !important; font-size: 0.95rem !important; transition: all 0.3s ease !important; }
    .stSelectbox > div > div { border-radius: 8px !important; border: 2px solid var(--border-color) !important; min-height: 45px !important; }
    .stButton > button { border-radius: 8px !important; padding: 0.75rem 2rem !important; font-weight: 600 !important; border: none !important; background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important; color: white !important; box-shadow: var(--shadow) !important; transition: all 0.3s ease !important; text-transform: uppercase; letter-spacing: 0.5px; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg) !important; }
    .stDownloadButton > button { background: linear-gradient(135deg, #10b981, #059669) !important; }
    .section-card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: var(--shadow); margin-bottom: 1.5rem; }
    .tipo-badge { display: inline-block; padding: 0.3rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600; background: linear-gradient(135deg, #1a2b4a, #C9A961); color: white; margin-bottom: 1rem; }
    .comercial-highlight { border-left: 4px solid #C9A961; padding-left: 1rem; background: #fffbf0; border-radius: 0 8px 8px 0; padding: 0.75rem 1rem; margin-bottom: 1rem; }
    @media (max-width: 768px) { .stButton > button { width: 100%; padding: 1rem !important; } .section-card { padding: 1rem; } }
</style>
""", unsafe_allow_html=True)

# ================= BANCO DE DADOS =================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS vistorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_imovel TEXT DEFAULT 'Residencial',
            subtipo_comercial TEXT,
            endereco TEXT NOT NULL,
            proprietario TEXT,
            inquilino TEXT,
            corretor_responsavel TEXT,
            tipo_vistoria TEXT,
            data_vistoria TEXT,
            hora_vistoria TEXT,
            dados_comodos TEXT,
            observacoes_gerais TEXT,
            status TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            data_modificacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migrações para bancos existentes
    for col, definition in [
        ("tipo_imovel",     "TEXT DEFAULT 'Residencial'"),
        ("subtipo_comercial", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE vistorias ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass  # Coluna já existe

    conn.commit()
    conn.close()


def get_vistorias(filtro_status=None, filtro_tipo=None, busca=None):
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT id, tipo_imovel, subtipo_comercial, endereco, proprietario,
               inquilino, tipo_vistoria, data_vistoria, status, data_criacao
        FROM vistorias WHERE 1=1
    """
    params = []
    if filtro_status and filtro_status != "Todos":
        query += " AND status = ?"; params.append(filtro_status)
    if filtro_tipo and filtro_tipo != "Todos":
        query += " AND tipo_vistoria = ?"; params.append(filtro_tipo)
    if busca:
        query += " AND (endereco LIKE ? OR proprietario LIKE ? OR inquilino LIKE ?)"
        params.extend([f"%{busca}%"] * 3)
    query += " ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def salvar_vistoria(dados, vistoria_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if vistoria_id:
        c.execute("""
            UPDATE vistorias SET
                tipo_imovel=?, subtipo_comercial=?, endereco=?, proprietario=?, inquilino=?,
                corretor_responsavel=?, tipo_vistoria=?, data_vistoria=?, hora_vistoria=?,
                dados_comodos=?, observacoes_gerais=?, status=?,
                data_modificacao=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            dados['tipo_imovel'], dados['subtipo_comercial'], dados['endereco'],
            dados['proprietario'], dados['inquilino'], dados['corretor_responsavel'],
            dados['tipo_vistoria'], dados['data_vistoria'], dados['hora_vistoria'],
            dados['dados_comodos'], dados['observacoes_gerais'], dados['status'],
            vistoria_id
        ))
    else:
        c.execute("""
            INSERT INTO vistorias (
                tipo_imovel, subtipo_comercial, endereco, proprietario, inquilino,
                corretor_responsavel, tipo_vistoria, data_vistoria, hora_vistoria,
                dados_comodos, observacoes_gerais, status
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            dados['tipo_imovel'], dados['subtipo_comercial'], dados['endereco'],
            dados['proprietario'], dados['inquilino'], dados['corretor_responsavel'],
            dados['tipo_vistoria'], dados['data_vistoria'], dados['hora_vistoria'],
            dados['dados_comodos'], dados['observacoes_gerais'], dados['status']
        ))
    conn.commit()
    conn.close()


def get_vistoria_by_id(vistoria_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM vistorias WHERE id=?", (vistoria_id,))
    row = c.fetchone()
    conn.close()
    return row


def deletar_vistoria(vistoria_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM vistorias WHERE id=?", (vistoria_id,))
    conn.commit()
    conn.close()


# ================= UTILITÁRIOS =================

def validar_dados(dados):
    erros = []
    if not dados.get('endereco') or len(dados['endereco']) < 10:
        erros.append("Endereço completo é obrigatório")
    if not dados.get('corretor_responsavel'):
        erros.append("Nome do corretor responsável é obrigatório")
    if not dados.get('tipo_vistoria'):
        erros.append("Tipo de vistoria é obrigatório")
    return erros


def get_config_imovel(tipo_imovel, subtipo_comercial):
    """Retorna a config (ícone + cômodos) para o tipo/subtipo selecionado."""
    if tipo_imovel == "Residencial":
        return CONFIGS_COMODOS["Residencial"]
    return CONFIGS_COMODOS.get(subtipo_comercial, CONFIGS_COMODOS["Outro Comercial"])


def nome_imovel_completo(tipo_imovel, subtipo_comercial):
    if tipo_imovel == "Residencial":
        return "Residencial"
    return subtipo_comercial or "Comercial"


# ================= GERAÇÃO DE PDF =================

def gerar_pdf_profissional(row):
    # Detecta o schema do banco (com ou sem colunas de migração)
    cols = [desc[0] for desc in sqlite3.connect(DB_NAME).execute("PRAGMA table_info(vistorias)").fetchall()]

    row_dict = dict(zip(cols, row))

    _id                = row_dict.get('id')
    tipo_imovel        = row_dict.get('tipo_imovel', 'Residencial')
    subtipo_comercial  = row_dict.get('subtipo_comercial', '')
    endereco           = row_dict.get('endereco', '')
    proprietario       = row_dict.get('proprietario', '')
    inquilino          = row_dict.get('inquilino', '')
    corretor           = row_dict.get('corretor_responsavel', '')
    tipo_vistoria      = row_dict.get('tipo_vistoria', '')
    data_vistoria      = row_dict.get('data_vistoria', '')
    hora_vistoria      = row_dict.get('hora_vistoria', '')
    dados_comodos_txt  = row_dict.get('dados_comodos', '{}')
    obs_gerais         = row_dict.get('observacoes_gerais', '')
    status             = row_dict.get('status', '')

    try:
        dados_comodos = json.loads(dados_comodos_txt)
    except Exception:
        dados_comodos = {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'],
        fontSize=22, textColor=colors.HexColor('#1a2b4a'),
        spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=12, textColor=colors.HexColor('#C9A961'),
        spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#1a2b4a'),
        spaceAfter=10, spaceBefore=14, fontName='Helvetica-Bold'
    )
    comodo_style = ParagraphStyle(
        'Comodo', parent=styles['Heading3'],
        fontSize=11, textColor=colors.HexColor('#1a2b4a'),
        spaceAfter=6, spaceBefore=8, fontName='Helvetica-Bold'
    )

    story = []

    # Título
    story.append(Paragraph("LAUDO DE VISTORIA DE IMÓVEL", title_style))
    subtitulo = nome_imovel_completo(tipo_imovel, subtipo_comercial)
    story.append(Paragraph(f"Imóvel {subtitulo}", subtitle_style))

    # Tabela de informações gerais
    info_data = [
        ['Endereço:', endereco],
        ['Tipo de Imóvel:', f"{tipo_imovel}" + (f" — {subtipo_comercial}" if subtipo_comercial else "")],
        ['Proprietário:', proprietario or 'Não informado'],
        ['Inquilino / Locatário:', inquilino or 'Não informado'],
        ['Corretor Responsável:', corretor],
        ['Tipo de Vistoria:', tipo_vistoria],
        ['Data / Hora:', f"{data_vistoria}  às  {hora_vistoria}"],
        ['Status:', status],
    ]
    info_table = Table(info_data, colWidths=[2.1*inch, 4.4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('PADDING',    (0, 0), (-1, -1), 8),
        ('GRID',       (0, 0), (-1, -1), 0.75, colors.HexColor('#e2e8f0')),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 18))

    # Resumo de ambientes
    if dados_comodos:
        story.append(Paragraph("AMBIENTES VISTORIADOS", heading_style))
        ambientes_resumo = [[nome, info.get('estado_geral', 'N/A')] for nome, info in dados_comodos.items()]
        if ambientes_resumo:
            header = [['Ambiente', 'Estado Geral']]
            resumo_table = Table(header + ambientes_resumo, colWidths=[4*inch, 2.5*inch])
            resumo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2b4a')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 10),
                ('PADDING',    (0, 0), (-1, -1), 8),
                ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            story.append(resumo_table)
            story.append(Spacer(1, 18))

    # Detalhamento por ambiente
    story.append(Paragraph("DETALHAMENTO POR AMBIENTE", heading_style))

    for comodo_nome, info in dados_comodos.items():
        story.append(Paragraph(f"📍 {comodo_nome}", comodo_style))

        estado_geral = info.get('estado_geral', 'N/A')
        obs          = info.get('observacoes', '')
        fotos_b64    = info.get('fotos', [])

        estado_data = [['Estado Geral'], [estado_geral]]

        # Cor do estado
        cor_estado = {
            'Excelente': colors.HexColor('#d1fae5'),
            'Bom':       colors.HexColor('#dbeafe'),
            'Regular':   colors.HexColor('#fef3c7'),
            'Ruim':      colors.HexColor('#fee2e2'),
            'Péssimo':   colors.HexColor('#fecaca'),
        }.get(estado_geral, colors.HexColor('#f1f5f9'))

        est_table = Table(estado_data, colWidths=[6.5*inch])
        est_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (0, 1), (-1, 1), cor_estado),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 10),
            ('PADDING',    (0, 0), (-1, -1), 7),
            ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(est_table)

        if obs:
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"<b>Observações:</b> {obs}", styles['Normal']))

        # Fotos
        if fotos_b64:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>Fotos:</b>", styles['Normal']))
            story.append(Spacer(1, 4))
            for idx, foto_str in enumerate(fotos_b64[:4]):
                try:
                    if foto_str:
                        # Remove prefixo data:image/...;base64,
                        if ',' in foto_str:
                            foto_str = foto_str.split(',', 1)[1]
                        img_data = base64.b64decode(foto_str)
                        img_buf = io.BytesIO(img_data)
                        PilImage.open(img_buf)   # valida
                        img_buf.seek(0)
                        img = RLImage(img_buf, width=2.5*inch, height=2*inch)
                        story.append(img)
                        story.append(Spacer(1, 4))
                except Exception:
                    story.append(Paragraph(f"<i>[Erro ao carregar foto {idx+1}]</i>", styles['Normal']))

        story.append(Spacer(1, 10))

    # Observações gerais
    story.append(Paragraph("OBSERVAÇÕES GERAIS", heading_style))
    story.append(Paragraph(obs_gerais or "Nenhuma observação adicional.", styles['Normal']))
    story.append(Spacer(1, 28))

    # Assinaturas
    story.append(Paragraph("ASSINATURAS", heading_style))
    story.append(Spacer(1, 16))
    assinaturas_data = [
        ['_________________________________', '_________________________________', '_________________________________'],
        ['Corretor Responsável', 'Proprietário', 'Inquilino / Locatário']
    ]
    assin_table = Table(assinaturas_data, colWidths=[2.1*inch]*3)
    assin_table.setStyle(TableStyle([
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE',  (0, 0), (-1, -1), 10),
        ('ALIGN',     (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(assin_table)

    story.append(Spacer(1, 28))
    story.append(Paragraph(
        f"<i>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ================= INTERFACE PRINCIPAL =================

def main():
    init_db()

    # Header
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        try:
            st.image("logo01.png", use_column_width=True)
        except Exception:
            st.warning("⚠️ Logo não encontrada. Adicione logo01.png na raiz do repositório.")

        st.markdown("""
            <div style="text-align:center;background:white;padding:1rem;border-radius:12px;
                        box-shadow:0 4px 6px rgba(0,0,0,0.1);margin-bottom:2rem;">
                <div style="font-size:1.8rem;font-weight:700;color:#1a2b4a;margin-top:0.5rem;">
                    Laudo de Vistoria
                </div>
                <div style="font-size:1rem;color:#64748b;margin-top:0.4rem;">
                    Sistema Profissional de Gestão de Vistorias Imobiliárias
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Estatísticas")
        df_all = get_vistorias()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", len(df_all))
        with col2:
            concluidas = len(df_all[df_all['status'] == 'Concluída']) if not df_all.empty else 0
            st.metric("Concluídas", concluidas)
        st.markdown("---")
        st.markdown("""
        ### 💡 Dicas de Uso
        - 📱 Use no celular para vistoriar no local
        - 💻 Acesse no desktop para revisar
        - 📸 Tire fotos durante a vistoria
        - 📄 Gere laudos em PDF profissionais
        """)

    tab1, tab2, tab3 = st.tabs(["📝 Nova Vistoria", "📋 Minhas Vistorias", "ℹ️ Ajuda"])

    # ==============================
    # TAB 1 — NOVA VISTORIA
    # ==============================
    with tab1:
        # IMPORTANTE: sem st.form para que a tela reaja em tempo real
        # quando o usuário altera as quantidades de ambientes.

        # --- TIPO DE IMÓVEL ---
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🏷️ Tipo de Imóvel")

        col_ti1, col_ti2 = st.columns(2)
        with col_ti1:
            tipo_imovel = st.selectbox(
                "Categoria do Imóvel *",
                ["Residencial", "Comercial"],
                key="tipo_imovel",
                help="Escolha se o imóvel é residencial ou comercial"
            )
        with col_ti2:
            if tipo_imovel == "Comercial":
                subtipo_comercial = st.selectbox(
                    "Subtipo Comercial *",
                    TIPOS_COMERCIAIS,
                    key="subtipo_comercial",
                    help="Selecione o tipo específico do imóvel comercial"
                )
                st.markdown(
                    f'<div class="comercial-highlight">🏢 Os <b>ambientes</b> serão configurados automaticamente para <b>{subtipo_comercial}</b>.</div>',
                    unsafe_allow_html=True
                )
            else:
                subtipo_comercial = None
                st.markdown(
                    '<div class="comercial-highlight">🏠 Vistoria padrão para imóvel <b>residencial</b> com quartos, salas, banheiros e demais cômodos.</div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

        # --- DADOS DO IMÓVEL ---
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🏢 Dados do Imóvel")

        col1, col2 = st.columns(2)
        with col1:
            endereco_rua         = st.text_input("Rua / Avenida *", placeholder="Ex: Rua das Flores", key="end_rua")
            endereco_numero      = st.text_input("Número *", placeholder="Ex: 123", key="end_num")
            endereco_complemento = st.text_input("Complemento", placeholder="Ex: Sala 45 / Loja A", key="end_comp")
            bairro               = st.text_input("Bairro *", placeholder="Ex: Centro", key="end_bairro")
        with col2:
            cidade    = st.text_input("Cidade *", placeholder="Ex: São Paulo", key="end_cidade")
            estado_uf = st.selectbox("Estado *", [
                "", "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA",
                "MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN",
                "RS","RO","RR","SC","SP","SE","TO"
            ], key="end_estado")
            cep = st.text_input("CEP", placeholder="Ex: 01234-567", key="end_cep")

        st.markdown('</div>', unsafe_allow_html=True)

        # --- PARTES ENVOLVIDAS ---
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👥 Partes Envolvidas")

        col3, col4, col5 = st.columns(3)
        with col3:
            proprietario = st.text_input("Proprietário", placeholder="Nome completo", key="proprietario")
        with col4:
            inquilino_label = "Inquilino / Locatário" if tipo_imovel == "Residencial" else "Empresa / Locatária"
            inquilino = st.text_input(inquilino_label, placeholder="Nome completo ou Razão Social", key="inquilino")
        with col5:
            corretor_responsavel = st.text_input("Corretor Responsável *", placeholder="Seu nome", key="corretor")

        st.markdown('</div>', unsafe_allow_html=True)

        # --- INFORMAÇÕES DA VISTORIA ---
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📅 Informações da Vistoria")

        col6, col7, col8 = st.columns(3)
        with col6:
            tipo_vistoria = st.selectbox("Tipo de Vistoria *",
                ["Entrada", "Saída", "Periódica", "Renovação"], key="tipo_vistoria")
        with col7:
            data_vistoria = st.date_input("Data *", value=datetime.now(), key="data_vistoria")
        with col8:
            hora_vistoria = st.time_input("Hora *", value=datetime.now().time(), key="hora_vistoria")

        st.markdown('</div>', unsafe_allow_html=True)

        # --- QUANTIDADES DE AMBIENTES (dinâmico) ---
        # Reage imediatamente pois não está dentro de st.form
        config        = get_config_imovel(tipo_imovel, subtipo_comercial)
        comodos_config = config["comodos"]
        icone_tipo    = config["icone"]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader(f"{icone_tipo} Quantidades de Ambientes")
        st.caption("Altere os números abaixo — os campos de detalhe aparecem automaticamente.")

        qtd_comodos = {}
        cols_qtd = st.columns(3)
        for idx, (chave, label) in enumerate(comodos_config.items()):
            with cols_qtd[idx % 3]:
                qtd_comodos[chave] = st.number_input(
                    label, min_value=0, max_value=20, step=1, value=0,
                    key=f"qtd_{chave}"
                )

        st.markdown('</div>', unsafe_allow_html=True)

        # --- DETALHAMENTO POR AMBIENTE (aparece ao vivo) ---
        ambientes_com_dados = [c for c, l in comodos_config.items() if int(qtd_comodos.get(c, 0)) > 0]

        if ambientes_com_dados:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🔍 Detalhamento por Ambiente")

        dados_comodos = {}

        for chave, label in comodos_config.items():
            quantidade = int(qtd_comodos.get(chave, 0))
            if quantidade == 0:
                continue

            label_singular = label.rstrip('s') if label.endswith('s') and not label.endswith('ss') else label

            with st.expander(f"{icone_tipo} {label} ({quantidade})", expanded=True):
                for i in range(quantidade):
                    nome_comodo = f"{label_singular} {i + 1}"
                    st.markdown(f"**{nome_comodo}**")

                    col_est, col_obs = st.columns([1, 2])
                    with col_est:
                        estado_geral = st.selectbox(
                            "Estado Geral",
                            ["Excelente", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"estado_{chave}_{i}",
                        )
                    with col_obs:
                        obs_comodo = st.text_area(
                            "Observações detalhadas",
                            key=f"obs_{chave}_{i}",
                            height=100,
                            placeholder="Descreva: paredes, teto, piso, portas, janelas, instalações, danos, etc."
                        )

                    fotos = st.file_uploader(
                        f"📷 Fotos — {nome_comodo}",
                        type=["png", "jpg", "jpeg"],
                        accept_multiple_files=True,
                        key=f"fotos_{chave}_{i}",
                    )

                    fotos_base64 = []
                    if fotos:
                        for foto in fotos:
                            img_bytes = foto.read()
                            img_b64 = base64.b64encode(img_bytes).decode()
                            fotos_base64.append(
                                f"data:image/{foto.type.split('/')[-1]};base64,{img_b64}"
                            )
                            st.image(img_bytes, caption=foto.name, width=200)

                    dados_comodos[nome_comodo] = {
                        "estado_geral": estado_geral,
                        "observacoes":  obs_comodo,
                        "fotos":        fotos_base64,
                    }

                    if i < quantidade - 1:
                        st.markdown("---")

        if ambientes_com_dados:
            st.markdown('</div>', unsafe_allow_html=True)

        # --- OBSERVAÇÕES FINAIS ---
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📝 Observações Gerais")

        observacoes_gerais = st.text_area(
            "Informações adicionais importantes",
            placeholder="Condições gerais do imóvel, acordos, pendências, etc.",
            height=150,
            key="obs_gerais"
        )
        status = st.selectbox(
            "Status da Vistoria",
            ["Concluída", "Pendente", "Problemas Identificados"],
            key="status_vistoria"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Botão salvar (st.button normal, não form_submit_button)
        col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
        with col_s2:
            submitted = st.button("💾 Salvar Vistoria", use_container_width=True, type="primary")

        if submitted:
            endereco_completo = f"{endereco_rua}, {endereco_numero}"
            if endereco_complemento:
                endereco_completo += f" - {endereco_complemento}"
            endereco_completo += f" - {bairro} - {cidade}/{estado_uf}"
            if cep:
                endereco_completo += f" - CEP: {cep}"

            dados = {
                'tipo_imovel':          tipo_imovel,
                'subtipo_comercial':    subtipo_comercial or '',
                'endereco':             endereco_completo,
                'proprietario':         proprietario,
                'inquilino':            inquilino,
                'corretor_responsavel': corretor_responsavel,
                'tipo_vistoria':        tipo_vistoria,
                'data_vistoria':        str(data_vistoria),
                'hora_vistoria':        str(hora_vistoria),
                'dados_comodos':        json.dumps(dados_comodos, ensure_ascii=False),
                'observacoes_gerais':   observacoes_gerais,
                'status':               status,
            }

            erros = validar_dados(dados)
            if erros:
                for erro in erros:
                    st.error(f"❌ {erro}")
            else:
                try:
                    salvar_vistoria(dados)
                    st.success("✅ Vistoria salva com sucesso! Acesse a aba 'Minhas Vistorias' para ver o registro.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {str(e)}")

    # ==============================
    # TAB 2 — LISTA DE VISTORIAS
    # ==============================
    with tab2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📋 Vistorias Cadastradas")

        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        with col_f1:
            busca = st.text_input("🔍 Buscar", placeholder="Endereço, proprietário ou inquilino...")
        with col_f2:
            filtro_status = st.selectbox("Status", ["Todos", "Concluída", "Pendente", "Problemas Identificados"])
        with col_f3:
            filtro_tipo = st.selectbox("Tipo de Vistoria", ["Todos", "Entrada", "Saída", "Periódica", "Renovação"])

        st.markdown('</div>', unsafe_allow_html=True)

        df = get_vistorias(
            filtro_status=filtro_status if filtro_status != "Todos" else None,
            filtro_tipo=filtro_tipo if filtro_tipo != "Todos" else None,
            busca=busca if busca else None
        )

        if df.empty:
            st.info("📭 Nenhuma vistoria encontrada. Crie sua primeira vistoria na aba 'Nova Vistoria'.")
        else:
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1: st.metric("Total", len(df))
            with col_s2: st.metric("Concluídas", len(df[df['status'] == 'Concluída']))
            with col_s3: st.metric("Pendentes",  len(df[df['status'] == 'Pendente']))
            with col_s4: st.metric("c/ Problemas", len(df[df['status'] == 'Problemas Identificados']))

            st.markdown("---")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id":               st.column_config.NumberColumn("ID", width="small"),
                    "tipo_imovel":      st.column_config.TextColumn("Categoria", width="small"),
                    "subtipo_comercial":st.column_config.TextColumn("Subtipo", width="medium"),
                    "endereco":         st.column_config.TextColumn("Endereço", width="large"),
                    "proprietario":     st.column_config.TextColumn("Proprietário", width="medium"),
                    "inquilino":        st.column_config.TextColumn("Inquilino", width="medium"),
                    "tipo_vistoria":    st.column_config.TextColumn("Tipo", width="small"),
                    "data_vistoria":    st.column_config.DateColumn("Data", width="small"),
                    "status":           st.column_config.TextColumn("Status", width="medium"),
                }
            )

            st.markdown("---")

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Ações")

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                vistoria_id = st.selectbox(
                    "Selecionar Vistoria",
                    df['id'].tolist(),
                    format_func=lambda x: f"ID {x} — {df[df['id']==x]['endereco'].values[0][:50]}..."
                )
            with col_a2:
                st.write("")
                st.write("")
                col_b1, col_b2, col_b3 = st.columns(3)

                with col_b1:
                    if st.button("📄 Gerar PDF", use_container_width=True):
                        row = get_vistoria_by_id(int(vistoria_id))
                        if row:
                            with st.spinner("Gerando PDF..."):
                                try:
                                    pdf_bytes = gerar_pdf_profissional(row)
                                    st.download_button(
                                        label="⬇️ Baixar PDF",
                                        data=pdf_bytes,
                                        file_name=f"vistoria_{vistoria_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                except Exception as e:
                                    st.error(f"Erro ao gerar PDF: {e}")

                with col_b2:
                    if st.button("📊 Exportar Excel", use_container_width=True):
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Vistorias')
                        buf.seek(0)
                        st.download_button(
                            label="⬇️ Baixar Excel",
                            data=buf,
                            file_name=f"vistorias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                with col_b3:
                    if st.button("🗑️ Excluir", type="secondary", use_container_width=True):
                        if st.checkbox(f"Confirmar exclusão da vistoria {vistoria_id}?"):
                            deletar_vistoria(int(vistoria_id))
                            st.success("✅ Vistoria excluída!")
                            st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # ==============================
    # TAB 3 — AJUDA
    # ==============================
    with tab3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("💡 Como Usar o Sistema")

        st.markdown("""
        ### 🏷️ Tipos de Imóvel Suportados
        | Categoria | Subtipos |
        |-----------|----------|
        | 🏠 Residencial | Padrão (quartos, sala, cozinha, banheiro…) |
        | 🏢 Comercial | Sala Comercial, Ponto Comercial, Loja, Galpão, Escritório, Consultório, Restaurante/Bar, Clínica/Laboratório, Outro |

        ### 🎯 Fluxo de Vistoria
        1. **Escolha o tipo de imóvel** — Residencial ou Comercial
        2. **Se Comercial**, selecione o subtipo (ex: Ponto Comercial)
        3. **Preencha os dados** do imóvel e das partes
        4. **Informe as quantidades** de cada ambiente
        5. **Detalhe cada ambiente** com estado, observações e fotos
        6. **Salve** e gere o **laudo em PDF**

        ### 💡 Dicas Importantes
        - ✅ Para um Ponto Comercial com copa e banheiro: informe 1 Salão, 1 Copa, 1 Banheiro
        - ✅ Os campos de quantidade que ficarem em **0** não aparecem no formulário nem no PDF
        - ✅ Tire fotos de ângulos diferentes — o PDF incluirá até 4 fotos por ambiente
        - ✅ Use as observações para registrar detalhes importantes de cada espaço

        ### 🔐 Sincronização de Dados
        O arquivo **vistoria.db** contém todos os dados. Para sincronizar entre dispositivos:
        - Opção 1: Serviço de cloud (Dropbox, Google Drive)
        - Opção 2: Backup regular do arquivo
        - Opção 3: Servidor compartilhado
        """)

        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
