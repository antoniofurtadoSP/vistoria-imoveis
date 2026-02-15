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

# Configuração da página - DEVE SER A PRIMEIRA CHAMADA STREAMLIT
st.set_page_config(
    page_title="Vistoria Imóveis Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para Interface Moderna e Responsiva
st.markdown("""
<style>
    /* Importando fontes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Variáveis de tema - Paleta AF */
    :root {
        --primary-color: #1a2b4a;
        --secondary-color: #C9A961;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --dark-bg: #1a2b4a;
        --light-bg: #f8fafc;
        --text-dark: #1a2b4a;
        --text-light: #64748b;
        --border-color: #e2e8f0;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --gold: #C9A961;
    }
    
    /* Reset e fonte base */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Títulos com Poppins */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-dark) !important;
    }
    
    /* Container principal */
    .main {
        padding: 1rem;
        background: linear-gradient(135deg, #1a2b4a 0%, #2d4a7c 100%);
        min-height: 100vh;
    }
    
    /* Cards modernos */
    .stApp {
        background: transparent;
    }
    
    /* Tabs estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        border-radius: 12px;
        padding: 0.5rem;
        box-shadow: var(--shadow);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        padding: 0 24px;
        font-weight: 500;
        background-color: transparent;
        border: none;
        color: var(--text-light);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
    }
    
    /* Inputs modernos */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 2px solid var(--border-color) !important;
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    /* Selectbox - corrigindo texto cortado */
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 2px solid var(--border-color) !important;
        min-height: 45px !important;
    }
    
    .stSelectbox > div > div > div {
        padding: 0.75rem !important;
        font-size: 0.95rem !important;
        line-height: 1.5 !important;
        min-height: 45px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Botões modernos */
    .stButton > button {
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        border: none !important;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        box-shadow: var(--shadow) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg) !important;
    }
    
    /* Download button específico */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--success-color), #059669) !important;
    }
    
    /* Expanders modernos */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 8px !important;
        border: 2px solid var(--border-color) !important;
        padding: 1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary-color) !important;
        background-color: #f8fafc !important;
    }
    
    /* DataFrames */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: white;
        border-radius: 8px;
        padding: 1rem;
        border: 2px dashed var(--border-color);
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: var(--primary-color);
        background-color: #f8fafc;
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 8px !important;
        border: none !important;
        box-shadow: var(--shadow) !important;
    }
    
    /* Cabeçalho customizado */
    .header-container {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #C9A961, #d4b76a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .app-subtitle {
        color: var(--text-light);
        font-size: 1.1rem;
    }
    
    /* Card de seção */
    .section-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
    }
    
    /* Mobile responsivo */
    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
        
        .header-container {
            padding: 1rem;
        }
        
        .app-title {
            font-size: 1.8rem;
        }
        
        .stButton > button {
            width: 100%;
            padding: 1rem !important;
        }
        
        .section-card {
            padding: 1rem;
        }
    }
    
    /* Badge de status */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-concluida {
        background-color: #d1fae5;
        color: #065f46;
    }
    
    .status-pendente {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-problemas {
        background-color: #fee2e2;
        color: #991b1b;
    }
    
    /* Preview de fotos */
    .photo-preview {
        display: inline-block;
        width: 100px;
        height: 100px;
        margin: 0.5rem;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }
    
    .photo-preview img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
</style>
""", unsafe_allow_html=True)

# ================= BANCO DE DADOS =================

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela principal de vistorias
    c.execute("""
        CREATE TABLE IF NOT EXISTS vistorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endereco TEXT NOT NULL,
            proprietario TEXT,
            inquilino TEXT,
            corretor_responsavel TEXT,
            tipo_vistoria TEXT,
            data_vistoria TEXT,
            hora_vistoria TEXT,
            quartos INTEGER DEFAULT 0,
            banheiros INTEGER DEFAULT 0,
            salas INTEGER DEFAULT 0,
            cozinhas INTEGER DEFAULT 0,
            areas_servico INTEGER DEFAULT 0,
            vagas_garagem INTEGER DEFAULT 0,
            dados_comodos TEXT,
            observacoes_gerais TEXT,
            status TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            data_modificacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def get_vistorias(filtro_status=None, filtro_tipo=None, busca=None):
    """Retorna lista de vistorias com filtros opcionais"""
    conn = sqlite3.connect(DB_NAME)
    
    query = """
        SELECT
            id,
            endereco,
            proprietario,
            inquilino,
            tipo_vistoria,
            data_vistoria,
            status,
            data_criacao
        FROM vistorias
        WHERE 1=1
    """
    params = []
    
    if filtro_status and filtro_status != "Todos":
        query += " AND status = ?"
        params.append(filtro_status)
    
    if filtro_tipo and filtro_tipo != "Todos":
        query += " AND tipo_vistoria = ?"
        params.append(filtro_tipo)
    
    if busca:
        query += " AND (endereco LIKE ? OR proprietario LIKE ? OR inquilino LIKE ?)"
        params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
    
    query += " ORDER BY id DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def salvar_vistoria(dados, vistoria_id=None):
    """Salva ou atualiza uma vistoria"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if vistoria_id:
        # Atualizar vistoria existente
        c.execute("""
            UPDATE vistorias SET
                endereco = ?,
                proprietario = ?,
                inquilino = ?,
                corretor_responsavel = ?,
                tipo_vistoria = ?,
                data_vistoria = ?,
                hora_vistoria = ?,
                quartos = ?,
                banheiros = ?,
                salas = ?,
                cozinhas = ?,
                areas_servico = ?,
                vagas_garagem = ?,
                dados_comodos = ?,
                observacoes_gerais = ?,
                status = ?,
                data_modificacao = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            dados['endereco'],
            dados['proprietario'],
            dados['inquilino'],
            dados['corretor_responsavel'],
            dados['tipo_vistoria'],
            dados['data_vistoria'],
            dados['hora_vistoria'],
            dados['quartos'],
            dados['banheiros'],
            dados['salas'],
            dados['cozinhas'],
            dados['areas_servico'],
            dados['vagas_garagem'],
            dados['dados_comodos'],
            dados['observacoes_gerais'],
            dados['status'],
            vistoria_id
        ))
    else:
        # Inserir nova vistoria
        c.execute("""
            INSERT INTO vistorias (
                endereco, proprietario, inquilino, corretor_responsavel,
                tipo_vistoria, data_vistoria, hora_vistoria,
                quartos, banheiros, salas, cozinhas, areas_servico, vagas_garagem,
                dados_comodos, observacoes_gerais, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dados['endereco'],
            dados['proprietario'],
            dados['inquilino'],
            dados['corretor_responsavel'],
            dados['tipo_vistoria'],
            dados['data_vistoria'],
            dados['hora_vistoria'],
            dados['quartos'],
            dados['banheiros'],
            dados['salas'],
            dados['cozinhas'],
            dados['areas_servico'],
            dados['vagas_garagem'],
            dados['dados_comodos'],
            dados['observacoes_gerais'],
            dados['status']
        ))
    
    conn.commit()
    conn.close()

def get_vistoria_by_id(vistoria_id):
    """Retorna uma vistoria específica pelo ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM vistorias WHERE id = ?", (vistoria_id,))
    row = c.fetchone()
    conn.close()
    return row

def deletar_vistoria(vistoria_id):
    """Deleta uma vistoria"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM vistorias WHERE id = ?", (vistoria_id,))
    conn.commit()
    conn.close()

# ================= UTILITÁRIOS =================

def salvar_foto(uploaded_file):
    """Converte foto para base64"""
    if uploaded_file:
        try:
            img = PilImage.open(uploaded_file)
            
            # Redimensionar para otimizar tamanho
            max_size = (1200, 1200)
            img.thumbnail(max_size, PilImage.Resampling.LANCZOS)
            
            # Converter para RGB se necessário
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Comprimir e salvar
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
            img_byte_arr = img_byte_arr.getvalue()
            
            return base64.b64encode(img_byte_arr).decode()
        except Exception as e:
            st.error(f"Erro ao processar foto: {str(e)}")
            return None
    return None

def validar_dados(dados):
    """Valida os dados antes de salvar"""
    erros = []
    
    if not dados.get('endereco') or len(dados['endereco']) < 10:
        erros.append("Endereço completo é obrigatório")
    
    if not dados.get('corretor_responsavel'):
        erros.append("Nome do corretor responsável é obrigatório")
    
    if not dados.get('tipo_vistoria'):
        erros.append("Tipo de vistoria é obrigatório")
    
    return erros

def gerar_pdf_profissional(row):
    """Gera PDF profissional e bem formatado"""
    (
        _id, endereco, proprietario, inquilino, corretor_responsavel,
        tipo_vistoria, data_vistoria, hora_vistoria,
        quartos, banheiros, salas, cozinhas, areas_servico, vagas_garagem,
        dados_comodos_texto, observacoes_gerais, status, *_
    ) = row

    try:
        dados_comodos = json.loads(dados_comodos_texto)
    except Exception:
        dados_comodos = {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Estilos customizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Título
    story.append(Paragraph("LAUDO DE VISTORIA DE IMÓVEL", title_style))
    story.append(Spacer(1, 20))

    # Informações principais em tabela
    info_data = [
        ['Endereço:', endereco],
        ['Proprietário:', proprietario or 'Não informado'],
        ['Inquilino:', inquilino or 'Não informado'],
        ['Corretor Responsável:', corretor_responsavel],
        ['Tipo de Vistoria:', tipo_vistoria],
        ['Data:', f"{data_vistoria}  às {hora_vistoria}"],
        ['Status:', status]
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1e293b')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Resumo de cômodos
    story.append(Paragraph("RESUMO DO IMÓVEL", heading_style))
    comodos_data = [
        ['Quartos', 'Banheiros', 'Salas', 'Cozinhas', 'Áreas de Serviço', 'Vagas Garagem'],
        [str(quartos), str(banheiros), str(salas), str(cozinhas), str(areas_servico), str(vagas_garagem)]
    ]
    
    comodos_table = Table(comodos_data, colWidths=[1.08*inch]*6)
    comodos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(comodos_table)
    story.append(Spacer(1, 20))

    # Detalhamento por cômodo
    story.append(Paragraph("DETALHAMENTO POR CÔMODO", heading_style))
    story.append(Spacer(1, 10))

    for comodo_nome, info in dados_comodos.items():
        if not info.get('estados'):
            continue
            
        story.append(Paragraph(f"<b>{comodo_nome}</b>", styles['Heading3']))
        
        estados = info.get('estados', {})
        obs = info.get('observacao', '')
        fotos_b64 = info.get('fotos', [])

        # Tabela de estados
        estados_data = [
            ['Paredes', 'Teto', 'Piso', 'Portas', 'Janelas', 'Móveis/Armários'],
            [
                estados.get('paredes', 'N/A'),
                estados.get('teto', 'N/A'),
                estados.get('piso', 'N/A'),
                estados.get('portas', 'N/A'),
                estados.get('janelas', 'N/A'),
                estados.get('moveis', 'N/A')
            ]
        ]
        
        estados_table = Table(estados_data, colWidths=[1.08*inch]*6)
        estados_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        story.append(estados_table)
        
        if obs:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>Observações:</b> {obs}", styles['Normal']))
        
        # Fotos
        if fotos_b64 and len(fotos_b64) > 0:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Fotos:</b>", styles['Normal']))
            story.append(Spacer(1, 4))
            
            fotos_adicionadas = 0
            for idx, foto_str in enumerate(fotos_b64[:4]):  # Máximo 4 fotos por cômodo
                try:
                    if foto_str and len(foto_str) > 0:
                        img_data = base64.b64decode(foto_str)
                        img_buffer = io.BytesIO(img_data)
                        # Tentar abrir com PIL primeiro para validar
                        pil_img = PilImage.open(img_buffer)
                        img_buffer.seek(0)  # Voltar ao início
                        img = RLImage(img_buffer, width=2.5*inch, height=2*inch)
                        story.append(img)
                        story.append(Spacer(1, 4))
                        fotos_adicionadas += 1
                except Exception as e:
                    # Adicionar mensagem de erro no PDF para debug
                    story.append(Paragraph(f"<i>[Erro ao carregar foto {idx+1}]</i>", styles['Normal']))
                    continue
            
            if fotos_adicionadas == 0:
                story.append(Paragraph("<i>Nenhuma foto foi carregada corretamente.</i>", styles['Normal']))

        story.append(Spacer(1, 12))

    # Observações gerais
    story.append(Paragraph("OBSERVAÇÕES GERAIS", heading_style))
    story.append(Paragraph(observacoes_gerais or "Nenhuma observação adicional.", styles['Normal']))
    story.append(Spacer(1, 30))

    # Assinaturas
    story.append(Paragraph("ASSINATURAS", heading_style))
    story.append(Spacer(1, 20))
    
    assinaturas_data = [
        ['_________________________________', '_________________________________', '_________________________________'],
        ['Corretor Responsável', 'Proprietário', 'Inquilino']
    ]
    
    assinaturas_table = Table(assinaturas_data, colWidths=[2.1*inch]*3)
    assinaturas_table.setStyle(TableStyle([
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(assinaturas_table)
    
    # Rodapé
    story.append(Spacer(1, 30))
    story.append(Paragraph(
        f"<i>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ================= INTERFACE PRINCIPAL =================

def main():
    # Inicializar banco de dados
    init_db()
    
    # Header com logo usando Streamlit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("https://raw.githubusercontent.com/antoniofurtadoSP/vistoria-imoveis/main/logo01.png", 
                     use_container_width=True)
        except:
            pass
        
        st.markdown("""
            <div style="text-align: center;">
                <div style="font-size: 1.8rem; font-weight: 700; color: #1a2b4a; margin-top: 0.5rem; margin-bottom: 0.5rem;">
                    Laudo de Vistoria
                </div>
                <div style="font-size: 1rem; color: #64748b;">
                    Sistema Profissional de Gestão de Vistorias Imobiliárias
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Sidebar com informações
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

    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📝 Nova Vistoria", "📋 Minhas Vistorias", "ℹ️ Ajuda"])

    # ========== TAB 1: NOVA VISTORIA ==========
    with tab1:
        with st.form("form_vistoria", clear_on_submit=True):
            # Seção: Dados do Imóvel
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🏢 Dados do Imóvel")
            
            col1, col2 = st.columns(2)
            with col1:
                endereco_rua = st.text_input("Rua / Avenida *", placeholder="Ex: Rua das Flores")
                endereco_numero = st.text_input("Número *", placeholder="Ex: 123")
                endereco_complemento = st.text_input("Complemento", placeholder="Ex: Apto 45")
                bairro = st.text_input("Bairro *", placeholder="Ex: Centro")
            
            with col2:
                cidade = st.text_input("Cidade *", placeholder="Ex: São Paulo")
                estado = st.selectbox("Estado *", [
                    "", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
                    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
                    "RS", "RO", "RR", "SC", "SP", "SE", "TO"
                ])
                cep = st.text_input("CEP", placeholder="Ex: 01234-567")
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Seção: Partes Envolvidas
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("👥 Partes Envolvidas")
            
            col3, col4, col5 = st.columns(3)
            with col3:
                proprietario = st.text_input("Nome do Proprietário", placeholder="Nome completo")
            with col4:
                inquilino = st.text_input("Nome do Inquilino", placeholder="Nome completo")
            with col5:
                corretor_responsavel = st.text_input("Corretor Responsável *", placeholder="Seu nome")
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Seção: Informações da Vistoria
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("📅 Informações da Vistoria")
            
            col6, col7, col8 = st.columns(3)
            with col6:
                tipo_vistoria = st.selectbox("Tipo de Vistoria *", 
                    ["Entrada", "Saída", "Periódica", "Renovação"])
            with col7:
                data_vistoria = st.date_input("Data *", value=datetime.now())
            with col8:
                hora_vistoria = st.time_input("Hora *", value=datetime.now().time())
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Seção: Características do Imóvel
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🔢 Características do Imóvel")
            
            col9, col10, col11 = st.columns(3)
            with col9:
                quartos = st.number_input("Quartos", min_value=0, max_value=20, step=1, value=0)
                banheiros = st.number_input("Banheiros", min_value=0, max_value=10, step=1, value=0)
            
            with col10:
                salas = st.number_input("Salas", min_value=0, max_value=10, step=1, value=0)
                cozinhas = st.number_input("Cozinhas", min_value=0, max_value=5, step=1, value=0)
            
            with col11:
                areas_servico = st.number_input("Áreas de Serviço", min_value=0, max_value=5, step=1, value=0)
                vagas_garagem = st.number_input("Vagas de Garagem", min_value=0, max_value=10, step=1, value=0)
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Seção: Detalhamento por Cômodo
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🔍 Detalhamento por Cômodo")
            
            comodos_lista = [
                "Sala de Estar", "Sala de Jantar", "Quarto 1", "Quarto 2", "Quarto 3",
                "Suíte", "Banheiro Social", "Banheiro Suíte", "Cozinha", 
                "Área de Serviço", "Garagem", "Varanda", "Quintal", "Outros"
            ]

            dados_comodos = {}

            for nome_comodo in comodos_lista:
                with st.expander(f"🚪 {nome_comodo}", expanded=False):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        paredes = st.selectbox(
                            "Paredes",
                            ["Não informado", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_paredes"
                        )
                        teto = st.selectbox(
                            "Teto",
                            ["Não informado", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_teto"
                        )
                        piso = st.selectbox(
                            "Piso",
                            ["Não informado", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_piso"
                        )
                    
                    with col_b:
                        portas = st.selectbox(
                            "Portas",
                            ["Não informado", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_portas"
                        )
                        janelas = st.selectbox(
                            "Janelas",
                            ["Não informado", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_janelas"
                        )
                        moveis = st.selectbox(
                            "Móveis/Armários",
                            ["Não se aplica", "Ótimo", "Bom", "Regular", "Ruim", "Péssimo"],
                            key=f"{nome_comodo}_moveis"
                        )

                    obs_comodo = st.text_area(
                        "Observações",
                        placeholder="Descreva detalhes, danos, reparos necessários, etc.",
                        key=f"{nome_comodo}_obs",
                        height=100
                    )

                    fotos_comodo_files = st.file_uploader(
                        "📸 Adicionar Fotos",
                        accept_multiple_files=True,
                        type=["jpg", "jpeg", "png"],
                        key=f"{nome_comodo}_fotos",
                        help="Você pode tirar fotos com a câmera do celular"
                    )

                    fotos_comodo_b64 = []
                    if fotos_comodo_files:
                        st.caption(f"✅ {len(fotos_comodo_files)} foto(s) adicionada(s)")
                        for f in fotos_comodo_files:
                            b64 = salvar_foto(f)
                            if b64:
                                fotos_comodo_b64.append(b64)

                    # Só salvar dados se pelo menos um campo foi preenchido
                    if any([
                        paredes != "Não informado",
                        teto != "Não informado",
                        piso != "Não informado",
                        portas != "Não informado",
                        janelas != "Não informado",
                        moveis != "Não se aplica",
                        obs_comodo,
                        fotos_comodo_b64
                    ]):
                        dados_comodos[nome_comodo] = {
                            "estados": {
                                "paredes": paredes,
                                "teto": teto,
                                "piso": piso,
                                "portas": portas,
                                "janelas": janelas,
                                "moveis": moveis,
                            },
                            "observacao": obs_comodo,
                            "fotos": fotos_comodo_b64,
                        }
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Seção: Observações Finais
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("📝 Observações Gerais")
            observacoes_gerais = st.text_area(
                "Informações adicionais importantes",
                placeholder="Descreva qualquer informação relevante sobre o imóvel, condições gerais, acordos, etc.",
                height=150
            )
            
            status = st.selectbox(
                "Status da Vistoria",
                ["Concluída", "Pendente", "Problemas Identificados"],
                help="Selecione o status atual da vistoria"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Botão de submit
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            with col_submit2:
                submitted = st.form_submit_button("💾 Salvar Vistoria", use_container_width=True)

            if submitted:
                # Montar endereço completo
                endereco_completo = f"{endereco_rua}, {endereco_numero}"
                if endereco_complemento:
                    endereco_completo += f" - {endereco_complemento}"
                endereco_completo += f" - {bairro} - {cidade}/{estado}"
                if cep:
                    endereco_completo += f" - CEP: {cep}"

                # Preparar dados
                dados = {
                    'endereco': endereco_completo,
                    'proprietario': proprietario,
                    'inquilino': inquilino,
                    'corretor_responsavel': corretor_responsavel,
                    'tipo_vistoria': tipo_vistoria,
                    'data_vistoria': str(data_vistoria),
                    'hora_vistoria': str(hora_vistoria),
                    'quartos': int(quartos),
                    'banheiros': int(banheiros),
                    'salas': int(salas),
                    'cozinhas': int(cozinhas),
                    'areas_servico': int(areas_servico),
                    'vagas_garagem': int(vagas_garagem),
                    'dados_comodos': json.dumps(dados_comodos, ensure_ascii=False),
                    'observacoes_gerais': observacoes_gerais,
                    'status': status
                }

                # Validar
                erros = validar_dados(dados)
                
                if erros:
                    for erro in erros:
                        st.error(f"❌ {erro}")
                else:
                    try:
                        salvar_vistoria(dados)
                        st.success("✅ Vistoria salva com sucesso!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar: {str(e)}")

    # ========== TAB 2: LISTA DE VISTORIAS ==========
    with tab2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📋 Vistorias Cadastradas")
        
        # Filtros
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        
        with col_f1:
            busca = st.text_input("🔍 Buscar", placeholder="Pesquisar por endereço, proprietário ou inquilino...")
        
        with col_f2:
            filtro_status = st.selectbox("Status", ["Todos", "Concluída", "Pendente", "Problemas Identificados"])
        
        with col_f3:
            filtro_tipo = st.selectbox("Tipo", ["Todos", "Entrada", "Saída", "Periódica", "Renovação"])
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Buscar vistorias
        df = get_vistorias(
            filtro_status=filtro_status if filtro_status != "Todos" else None,
            filtro_tipo=filtro_tipo if filtro_tipo != "Todos" else None,
            busca=busca if busca else None
        )

        if df.empty:
            st.info("📭 Nenhuma vistoria encontrada. Crie sua primeira vistoria na aba 'Nova Vistoria'.")
        else:
            # Estatísticas rápidas
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("Total", len(df))
            with col_stat2:
                concluidas = len(df[df['status'] == 'Concluída'])
                st.metric("Concluídas", concluidas)
            with col_stat3:
                pendentes = len(df[df['status'] == 'Pendente'])
                st.metric("Pendentes", pendentes)
            with col_stat4:
                problemas = len(df[df['status'] == 'Problemas Identificados'])
                st.metric("c/ Problemas", problemas)

            st.markdown("---")

            # Exibir tabela
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "endereco": st.column_config.TextColumn("Endereço", width="large"),
                    "proprietario": st.column_config.TextColumn("Proprietário", width="medium"),
                    "inquilino": st.column_config.TextColumn("Inquilino", width="medium"),
                    "tipo_vistoria": st.column_config.TextColumn("Tipo", width="small"),
                    "data_vistoria": st.column_config.DateColumn("Data", width="small"),
                    "status": st.column_config.TextColumn("Status", width="medium"),
                }
            )

            st.markdown("---")

            # Ações
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Ações")
            
            col_action1, col_action2 = st.columns(2)
            
            with col_action1:
                vistoria_id = st.selectbox(
                    "Selecionar Vistoria",
                    df['id'].tolist(),
                    format_func=lambda x: f"ID {x} - {df[df['id']==x]['endereco'].values[0][:50]}..."
                )
            
            with col_action2:
                st.write("")  # Espaçamento
                st.write("")  # Espaçamento
                
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("📄 Gerar PDF", use_container_width=True):
                        row = get_vistoria_by_id(int(vistoria_id))
                        if row:
                            with st.spinner("Gerando PDF..."):
                                pdf_bytes = gerar_pdf_profissional(row)
                                st.download_button(
                                    label="⬇️ Baixar PDF",
                                    data=pdf_bytes,
                                    file_name=f"vistoria_{vistoria_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                
                with col_btn2:
                    if st.button("📊 Exportar Excel", use_container_width=True):
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Vistorias')
                        buffer.seek(0)
                        
                        st.download_button(
                            label="⬇️ Baixar Excel",
                            data=buffer,
                            file_name=f"vistorias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                
                with col_btn3:
                    if st.button("🗑️ Excluir", type="secondary", use_container_width=True):
                        if st.checkbox(f"Confirmar exclusão da vistoria {vistoria_id}?"):
                            deletar_vistoria(int(vistoria_id))
                            st.success("✅ Vistoria excluída!")
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

    # ========== TAB 3: AJUDA ==========
    with tab3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("💡 Como Usar o Sistema")
        
        st.markdown("""
        ### 📱 Acesso Mobile
        1. **Abra o app no navegador do celular**
        2. **Adicione à tela inicial** para acesso rápido
        3. **Use a câmera** para tirar fotos durante a vistoria
        4. **Salve na nuvem** - os dados ficam sincronizados
        
        ### 💻 Acesso Desktop
        1. **Revise as vistorias** com mais comodidade
        2. **Gere laudos em PDF** profissionais
        3. **Exporte para Excel** para análises
        4. **Gerencie** todas as vistorias
        
        ### 🎯 Dicas Importantes
        - ✅ Preencha todos os campos obrigatórios (marcados com *)
        - ✅ Tire fotos de ângulos diferentes de cada cômodo
        - ✅ Seja detalhado nas observações
        - ✅ Revise antes de salvar
        - ✅ Gere o PDF logo após concluir
        
        ### 🔐 Sincronização de Dados
        O arquivo **vistoria.db** contém todos os dados. Para sincronizar:
        - **Opção 1:** Use um serviço de cloud (Dropbox, Google Drive)
        - **Opção 2:** Faça backup regular do arquivo
        - **Opção 3:** Configure um servidor compartilhado
        
        ### 📞 Suporte
        Em caso de dúvidas ou problemas, entre em contato com o suporte técnico.
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
