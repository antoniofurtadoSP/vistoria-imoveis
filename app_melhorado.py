import streamlit as st
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from PIL import Image as PilImage
import io
import base64
import pandas as pd
import json

# ================= CONFIGURAÇÕES =================

DB_NAME = "vistoria.db"

st.set_page_config(
    page_title="Vistoria Imóveis Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CONFIGS DE IMÓVEIS =================

TIPOS_COMERCIAIS = [
    "Sala Comercial", "Ponto Comercial", "Loja", "Galpão",
    "Escritório", "Consultório", "Restaurante/Bar",
    "Clínica/Laboratório", "Outro Comercial",
]

CONFIGS_COMODOS = {
    "Residencial": {
        "icone": "🏠",
        "comodos": {
            "quartos": "Quartos", "banheiros": "Banheiros",
            "salas": "Salas", "cozinhas": "Cozinhas",
            "areas_servico": "Áreas de Serviço", "vagas_garagem": "Vagas de Garagem",
        },
    },
    "Sala Comercial": {
        "icone": "🏢",
        "comodos": {
            "recepcao": "Recepções", "sala_reuniao": "Salas de Reunião",
            "escritorio": "Escritórios/Estações", "banheiro": "Banheiros",
            "copa": "Copas", "deposito": "Depósitos",
        },
    },
    "Ponto Comercial": {
        "icone": "🏪",
        "comodos": {
            "salao": "Salões Principais", "copa": "Copas",
            "banheiro": "Banheiros", "deposito": "Depósitos",
        },
    },
    "Loja": {
        "icone": "🛍️",
        "comodos": {
            "salao_vendas": "Salões de Vendas", "provador": "Provadores",
            "banheiro": "Banheiros", "copa": "Copas", "deposito": "Depósitos/Estoque",
        },
    },
    "Galpão": {
        "icone": "🏭",
        "comodos": {
            "area_producao": "Áreas de Produção/Industrial", "escritorio": "Escritórios",
            "banheiro": "Banheiros", "refeitorio": "Refeitórios",
            "deposito": "Depósitos", "doca": "Docas/Carregamento",
        },
    },
    "Escritório": {
        "icone": "💼",
        "comodos": {
            "sala_trabalho": "Salas de Trabalho", "sala_reuniao": "Salas de Reunião",
            "recepcao": "Recepções", "banheiro": "Banheiros", "copa": "Copas",
        },
    },
    "Consultório": {
        "icone": "🩺",
        "comodos": {
            "sala_espera": "Salas de Espera", "consultorio": "Consultórios",
            "recepcao": "Recepções", "banheiro": "Banheiros", "copa": "Copas",
        },
    },
    "Restaurante/Bar": {
        "icone": "🍽️",
        "comodos": {
            "salao_atendimento": "Salões de Atendimento", "cozinha": "Cozinhas",
            "banheiro": "Banheiros", "deposito": "Depósitos/Despensas",
            "area_externa": "Áreas Externas",
        },
    },
    "Clínica/Laboratório": {
        "icone": "🏥",
        "comodos": {
            "sala_espera": "Salas de Espera", "sala_atend": "Salas de Atendimento",
            "laboratorio": "Laboratórios/Exames", "recepcao": "Recepções",
            "banheiro": "Banheiros", "copa": "Copas", "deposito": "Depósitos/Almoxarifado",
        },
    },
    "Outro Comercial": {
        "icone": "🏗️",
        "comodos": {
            "ambiente": "Ambientes Principais", "banheiro": "Banheiros",
            "copa": "Copas", "deposito": "Depósitos", "outro": "Outros Ambientes",
        },
    },
}

# ================= CSS =================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    :root {
        --primary-color: #1a2b4a;
        --secondary-color: #C9A961;
        --border-color: #e2e8f0;
        --shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    h1,h2,h3,h4,h5,h6 { font-family:'Poppins',sans-serif !important; font-weight:600 !important; color:#1a2b4a !important; }
    .stTabs [data-baseweb="tab-list"] { gap:8px; background:white; border-radius:12px; padding:0.5rem; box-shadow:var(--shadow); }
    .stTabs [data-baseweb="tab"] { height:50px; border-radius:8px; padding:0 24px; font-weight:500; background:transparent; border:none; color:#64748b; }
    .stTabs [aria-selected="true"] { background:linear-gradient(135deg,var(--primary-color),var(--secondary-color)) !important; color:white !important; }
    .stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea>div>div>textarea { border-radius:8px !important; border:2px solid var(--border-color) !important; padding:0.75rem !important; font-size:0.95rem !important; }
    .stSelectbox>div>div { border-radius:8px !important; border:2px solid var(--border-color) !important; min-height:45px !important; }
    .stButton>button { border-radius:8px !important; padding:0.75rem 2rem !important; font-weight:600 !important; border:none !important; background:linear-gradient(135deg,var(--primary-color),var(--secondary-color)) !important; color:white !important; box-shadow:var(--shadow) !important; transition:all 0.3s ease !important; text-transform:uppercase; letter-spacing:0.5px; }
    .stButton>button:hover { transform:translateY(-2px); box-shadow:var(--shadow-lg) !important; }
    .stDownloadButton>button { background:linear-gradient(135deg,#10b981,#059669) !important; }
    .section-card { background:white; padding:1.5rem; border-radius:12px; box-shadow:var(--shadow); margin-bottom:1.5rem; }
    .comercial-highlight { border-left:4px solid #C9A961; background:#fffbf0; border-radius:0 8px 8px 0; padding:0.75rem 1rem; margin-bottom:1rem; }
    .rascunho-banner { background:linear-gradient(135deg,#fff7ed,#fef3c7); border:2px solid #f59e0b; border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1.5rem; }
    .salvo-banner { background:linear-gradient(135deg,#f0fdf4,#dcfce7); border:2px solid #10b981; border-radius:12px; padding:0.8rem 1.2rem; margin-bottom:1rem; font-size:0.9rem; color:#065f46; }
    @media (max-width:768px) { .stButton>button { width:100%; padding:1rem !important; } .section-card { padding:1rem; } }
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
    for col, definition in [
        ("tipo_imovel", "TEXT DEFAULT 'Residencial'"),
        ("subtipo_comercial", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE vistorias ADD COLUMN {col} {definition}")
        except sqlite3.OperationalError:
            pass
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


def get_rascunhos():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, tipo_imovel, subtipo_comercial, endereco,
               corretor_responsavel, data_vistoria, data_modificacao
        FROM vistorias WHERE status = 'Rascunho'
        ORDER BY data_modificacao DESC
    """, conn)
    conn.close()
    return df


def salvar_vistoria(dados, vistoria_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if vistoria_id:
        c.execute("""
            UPDATE vistorias SET
                tipo_imovel=?, subtipo_comercial=?, endereco=?, proprietario=?,
                inquilino=?, corretor_responsavel=?, tipo_vistoria=?,
                data_vistoria=?, hora_vistoria=?, dados_comodos=?,
                observacoes_gerais=?, status=?,
                data_modificacao=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            dados['tipo_imovel'], dados['subtipo_comercial'], dados['endereco'],
            dados['proprietario'], dados['inquilino'], dados['corretor_responsavel'],
            dados['tipo_vistoria'], dados['data_vistoria'], dados['hora_vistoria'],
            dados['dados_comodos'], dados['observacoes_gerais'], dados['status'],
            vistoria_id
        ))
        conn.commit(); conn.close()
        return vistoria_id
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
        new_id = c.lastrowid
        conn.commit(); conn.close()
        return new_id


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
    conn.commit(); conn.close()


# ================= SESSION STATE =================

def init_session_state():
    defaults = {
        "rascunho_id":         None,
        "ultimo_auto_save":    None,
        "vistoria_finalizada": False,
        "modo_edicao":         False,   # True quando editando vistoria concluída
        "status_original":     None,    # Status antes de editar
        "ir_para_tab1":        False,   # Sinaliza para mostrar aviso na tab1
        "f_tipo_imovel":       "Residencial",
        "f_subtipo_comercial": "Ponto Comercial",
        "f_end_rua":           "",
        "f_end_numero":        "",
        "f_end_complemento":   "",
        "f_bairro":            "",
        "f_cidade":            "",
        "f_estado_uf":         "",
        "f_cep":               "",
        "f_proprietario":      "",
        "f_inquilino":         "",
        "f_corretor":          "",
        "f_tipo_vistoria":     "Entrada",
        "f_data_vistoria":     datetime.now().date(),
        "f_hora_vistoria":     datetime.now().time(),
        "f_qtd_comodos":       {},
        "f_dados_comodos":     {},
        "f_obs_gerais":        "",
        "f_status":            "Concluída",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def limpar_formulario():
    for key in list(st.session_state.keys()):
        if key.startswith("f_") or key.startswith("w_") or key in (
            "rascunho_id", "ultimo_auto_save", "vistoria_finalizada",
            "modo_edicao", "status_original", "ir_para_tab1"
        ):
            del st.session_state[key]
    init_session_state()


def get_config_imovel(tipo_imovel, subtipo_comercial):
    if tipo_imovel == "Residencial":
        return CONFIGS_COMODOS["Residencial"]
    return CONFIGS_COMODOS.get(subtipo_comercial, CONFIGS_COMODOS["Outro Comercial"])


def nome_imovel_completo(tipo_imovel, subtipo_comercial):
    return "Residencial" if tipo_imovel == "Residencial" else (subtipo_comercial or "Comercial")


def carregar_rascunho_no_estado(vistoria_id):
    row = get_vistoria_by_id(vistoria_id)
    if not row:
        return False
    cols = [desc[1] for desc in sqlite3.connect(DB_NAME).execute("PRAGMA table_info(vistorias)").fetchall()]
    d = dict(zip(cols, row))

    try:
        dados_comodos = json.loads(d.get('dados_comodos', '{}'))
    except Exception:
        dados_comodos = {}

    try:
        data_v = datetime.strptime(d.get('data_vistoria', ''), '%Y-%m-%d').date()
    except Exception:
        data_v = datetime.now().date()
    try:
        hora_v = datetime.strptime(d.get('hora_vistoria', ''), '%H:%M:%S').time()
    except Exception:
        hora_v = datetime.now().time()

    # Reconstruir quantidades
    tipo_im = d.get('tipo_imovel', 'Residencial')
    sub_im  = d.get('subtipo_comercial', '') or ''
    config  = get_config_imovel(tipo_im, sub_im)
    qtd = {}
    for chave, label in config["comodos"].items():
        label_s = label.rstrip('s') if label.endswith('s') and not label.endswith('ss') else label
        count = sum(1 for k in dados_comodos if k.startswith(label_s))
        if count > 0:
            qtd[chave] = count

    st.session_state.rascunho_id         = vistoria_id
    st.session_state.f_tipo_imovel       = tipo_im
    st.session_state.f_subtipo_comercial = sub_im if sub_im in TIPOS_COMERCIAIS else "Ponto Comercial"
    st.session_state.f_proprietario      = d.get('proprietario', '') or ''
    st.session_state.f_inquilino         = d.get('inquilino', '') or ''
    st.session_state.f_corretor          = d.get('corretor_responsavel', '') or ''
    st.session_state.f_tipo_vistoria     = d.get('tipo_vistoria', 'Entrada') or 'Entrada'
    st.session_state.f_data_vistoria     = data_v
    st.session_state.f_hora_vistoria     = hora_v
    st.session_state.f_qtd_comodos       = qtd
    st.session_state.f_dados_comodos     = dados_comodos
    st.session_state.f_obs_gerais        = d.get('observacoes_gerais', '') or ''
    st.session_state.f_status            = 'Concluída'

    # Tentar separar endereço
    end_raw = d.get('endereco', '')
    partes  = [p.strip() for p in end_raw.split(' - ')]
    rua_num = partes[0].rsplit(',', 1) if partes else ['', '']
    st.session_state.f_end_rua    = rua_num[0].strip()
    st.session_state.f_end_numero = rua_num[1].strip() if len(rua_num) > 1 else ''
    st.session_state.f_bairro     = partes[1] if len(partes) > 1 else ''
    if len(partes) > 2:
        cidade_uf = partes[2].split('/')
        st.session_state.f_cidade    = cidade_uf[0].strip()
        st.session_state.f_estado_uf = cidade_uf[1].strip() if len(cidade_uf) > 1 else ''
    return True


def montar_dados(dados_comodos_atual, status_override=None):
    s = st.session_state
    end = f"{s.f_end_rua}, {s.f_end_numero}"
    if s.f_end_complemento:
        end += f" - {s.f_end_complemento}"
    end += f" - {s.f_bairro} - {s.f_cidade}/{s.f_estado_uf}"
    if s.f_cep:
        end += f" - CEP: {s.f_cep}"
    return {
        'tipo_imovel':          s.f_tipo_imovel,
        'subtipo_comercial':    s.f_subtipo_comercial if s.f_tipo_imovel == 'Comercial' else '',
        'endereco':             end,
        'proprietario':         s.f_proprietario,
        'inquilino':            s.f_inquilino,
        'corretor_responsavel': s.f_corretor,
        'tipo_vistoria':        s.f_tipo_vistoria,
        'data_vistoria':        str(s.f_data_vistoria),
        'hora_vistoria':        str(s.f_hora_vistoria),
        'dados_comodos':        json.dumps(dados_comodos_atual, ensure_ascii=False),
        'observacoes_gerais':   s.f_obs_gerais,
        'status':               status_override or s.f_status,
    }


def auto_salvar(dados_comodos_atual):
    s = st.session_state
    # Não auto-salvar se estiver editando vistoria concluída sem ter feito alterações ainda
    # (evita mudar status para Rascunho sem querer)
    if s.modo_edicao and s.ultimo_auto_save is None:
        return
    tem_dados = (
        bool(s.f_end_rua) or bool(s.f_corretor) or bool(s.f_proprietario) or
        bool(dados_comodos_atual) or
        any(v > 0 for v in (s.f_qtd_comodos or {}).values())
    )
    if not tem_dados:
        return
    agora  = datetime.now()
    ultimo = s.ultimo_auto_save
    if ultimo and (agora - ultimo).seconds < 30:
        return
    dados  = montar_dados(dados_comodos_atual, status_override='Rascunho')
    novo_id = salvar_vistoria(dados, vistoria_id=s.rascunho_id)
    st.session_state.rascunho_id      = novo_id
    st.session_state.ultimo_auto_save = agora


def validar_dados(dados):
    erros = []
    if not dados.get('endereco') or len(dados['endereco']) < 10:
        erros.append("Endereço completo é obrigatório (Rua, Número, Bairro, Cidade)")
    if not dados.get('corretor_responsavel'):
        erros.append("Nome do corretor responsável é obrigatório")
    if not dados.get('tipo_vistoria'):
        erros.append("Tipo de vistoria é obrigatório")
    return erros


def formatar_data(data_str):
    """Converte YYYY-MM-DD para DD/MM/YYYY para exibição."""
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return data_str or ''


# ================= GERAÇÃO DE PDF =================

def gerar_pdf_profissional(row):
    cols = [desc[1] for desc in sqlite3.connect(DB_NAME).execute("PRAGMA table_info(vistorias)").fetchall()]
    d = dict(zip(cols, row))

    try:
        dados_comodos = json.loads(d.get('dados_comodos', '{}'))
    except Exception:
        dados_comodos = {}

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    title_style   = ParagraphStyle('T',  parent=styles['Heading1'], fontSize=22,
                                   textColor=colors.HexColor('#1a2b4a'), spaceAfter=6,
                                   alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_style     = ParagraphStyle('S',  parent=styles['Normal'],   fontSize=12,
                                   textColor=colors.HexColor('#C9A961'), spaceAfter=20,
                                   alignment=TA_CENTER, fontName='Helvetica-Bold')
    heading_style = ParagraphStyle('H',  parent=styles['Heading2'], fontSize=13,
                                   textColor=colors.HexColor('#1a2b4a'), spaceAfter=10,
                                   spaceBefore=14, fontName='Helvetica-Bold')
    comodo_style  = ParagraphStyle('C',  parent=styles['Heading3'], fontSize=11,
                                   textColor=colors.HexColor('#1a2b4a'), spaceAfter=6,
                                   spaceBefore=8,  fontName='Helvetica-Bold')

    story = []
    story.append(Paragraph("LAUDO DE VISTORIA DE IMÓVEL", title_style))
    story.append(Paragraph(f"Imóvel {nome_imovel_completo(d.get('tipo_imovel','Residencial'), d.get('subtipo_comercial',''))}", sub_style))

    info_data = [
        ['Endereço:',            d.get('endereco','')],
        ['Tipo de Imóvel:',      d.get('tipo_imovel','') + (f" — {d.get('subtipo_comercial','')}" if d.get('subtipo_comercial') else '')],
        ['Proprietário:',        d.get('proprietario','') or 'Não informado'],
        ['Inquilino/Locatário:', d.get('inquilino','')    or 'Não informado'],
        ['Corretor:',            d.get('corretor_responsavel','')],
        ['Tipo de Vistoria:',    d.get('tipo_vistoria','')],
        ['Data / Hora:',         f"{formatar_data(d.get('data_vistoria',''))}  às  {d.get('hora_vistoria','')[:5]}"],
        ['Status:',              d.get('status','')],
    ]
    t = Table(info_data, colWidths=[2.1*inch, 4.4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f1f5f9')),
        ('FONTNAME',  (0,0),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',  (1,0),(1,-1),'Helvetica'),
        ('FONTSIZE',  (0,0),(-1,-1),10),
        ('PADDING',   (0,0),(-1,-1),8),
        ('GRID',      (0,0),(-1,-1),0.75,colors.HexColor('#e2e8f0')),
        ('VALIGN',    (0,0),(-1,-1),'TOP'),
    ]))
    story.append(t); story.append(Spacer(1,18))

    if dados_comodos:
        story.append(Paragraph("AMBIENTES VISTORIADOS", heading_style))
        resumo = [[n, i.get('estado_geral','N/A')] for n,i in dados_comodos.items()]
        rt = Table([['Ambiente','Estado Geral']] + resumo, colWidths=[4*inch,2.5*inch])
        rt.setStyle(TableStyle([
            ('BACKGROUND',   (0,0),(-1,0),colors.HexColor('#1a2b4a')),
            ('TEXTCOLOR',    (0,0),(-1,0),colors.whitesmoke),
            ('FONTNAME',     (0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',     (0,0),(-1,-1),10),
            ('PADDING',      (0,0),(-1,-1),8),
            ('GRID',         (0,0),(-1,-1),0.5,colors.HexColor('#e2e8f0')),
            ('ALIGN',        (0,0),(-1,-1),'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8fafc')]),
        ]))
        story.append(rt); story.append(Spacer(1,18))

    story.append(Paragraph("DETALHAMENTO POR AMBIENTE", heading_style))
    for nome, info in dados_comodos.items():
        story.append(Paragraph(f"📍 {nome}", comodo_style))
        estado  = info.get('estado_geral','N/A')
        obs     = info.get('observacoes','')
        fotos   = info.get('fotos',[])

        cor = {'Excelente':colors.HexColor('#d1fae5'),'Bom':colors.HexColor('#dbeafe'),
               'Regular':colors.HexColor('#fef3c7'),'Ruim':colors.HexColor('#fee2e2'),
               'Péssimo':colors.HexColor('#fecaca')}.get(estado, colors.HexColor('#f1f5f9'))

        et = Table([['Estado Geral'],[estado]], colWidths=[6.5*inch])
        et.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f1f5f9')),
            ('BACKGROUND',(0,1),(-1,1),cor),
            ('FONTNAME',  (0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',  (0,0),(-1,-1),10),
            ('PADDING',   (0,0),(-1,-1),7),
            ('GRID',      (0,0),(-1,-1),0.5,colors.HexColor('#e2e8f0')),
            ('ALIGN',     (0,0),(-1,-1),'CENTER'),
        ]))
        story.append(et)
        if obs:
            story.append(Spacer(1,5))
            story.append(Paragraph(f"<b>Observações:</b> {obs}", styles['Normal']))
        if fotos:
            story.append(Spacer(1,6))
            story.append(Paragraph("<b>Fotos:</b>", styles['Normal']))
            story.append(Spacer(1,4))
            # Montar imagens em linhas de 3
            imgs_renderizadas = []
            for idx, fs in enumerate(fotos[:9]):  # máximo 9 fotos (3 linhas)
                try:
                    if ',' in fs: fs = fs.split(',',1)[1]
                    buf2 = io.BytesIO(base64.b64decode(fs))
                    PilImage.open(buf2); buf2.seek(0)
                    imgs_renderizadas.append(RLImage(buf2, width=2.0*inch, height=1.6*inch))
                except Exception:
                    imgs_renderizadas.append(Paragraph(f"<i>[Foto {idx+1}]</i>", styles['Normal']))
            # Agrupar em linhas de 3
            for i in range(0, len(imgs_renderizadas), 3):
                linha = imgs_renderizadas[i:i+3]
                # Completar a linha com células vazias se necessário
                while len(linha) < 3:
                    linha.append("")
                foto_table = Table([linha], colWidths=[2.1*inch]*3)
                foto_table.setStyle(TableStyle([
                    ('ALIGN',   (0,0),(-1,-1),'CENTER'),
                    ('VALIGN',  (0,0),(-1,-1),'MIDDLE'),
                    ('PADDING', (0,0),(-1,-1),4),
                ]))
                story.append(foto_table)
                story.append(Spacer(1,4))
        story.append(Spacer(1,10))

    story.append(Paragraph("OBSERVAÇÕES GERAIS", heading_style))
    story.append(Paragraph(d.get('observacoes_gerais','') or "Nenhuma observação adicional.", styles['Normal']))
    story.append(Spacer(1,28))
    story.append(Paragraph("ASSINATURAS", heading_style))
    story.append(Spacer(1,16))
    at = Table([
        ['_________________________________','_________________________________','_________________________________'],
        ['Corretor Responsável','Proprietário','Inquilino / Locatário']
    ], colWidths=[2.1*inch]*3)
    at.setStyle(TableStyle([
        ('FONTNAME',(0,1),(-1,1),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('ALIGN',  (0,0),(-1,-1),'CENTER'),
    ]))
    story.append(at)
    story.append(Spacer(1,28))
    story.append(Paragraph(
        f"<i>Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</i>",
        ParagraphStyle('F', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ================= FORMULÁRIO =================

def renderizar_formulario():
    """Renderiza todo o formulário usando session_state. Retorna dados_comodos."""
    s = st.session_state

    # TIPO DE IMÓVEL
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🏷️ Tipo de Imóvel")
    c1, c2 = st.columns(2)
    with c1:
        ti_idx      = ["Residencial","Comercial"].index(s.f_tipo_imovel) if s.f_tipo_imovel in ["Residencial","Comercial"] else 0
        tipo_imovel = st.selectbox("Categoria *", ["Residencial","Comercial"], index=ti_idx, key="w_tipo")
        s.f_tipo_imovel = tipo_imovel
    with c2:
        if tipo_imovel == "Comercial":
            sub_idx = TIPOS_COMERCIAIS.index(s.f_subtipo_comercial) if s.f_subtipo_comercial in TIPOS_COMERCIAIS else 0
            subtipo = st.selectbox("Subtipo Comercial *", TIPOS_COMERCIAIS, index=sub_idx, key="w_subtipo")
            s.f_subtipo_comercial = subtipo
            st.markdown(f'<div class="comercial-highlight">🏢 Configurado para <b>{subtipo}</b></div>', unsafe_allow_html=True)
        else:
            subtipo = None
            st.markdown('<div class="comercial-highlight">🏠 Vistoria padrão <b>residencial</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # DADOS DO IMÓVEL
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("🏢 Dados do Imóvel")
    c1, c2 = st.columns(2)
    with c1:
        s.f_end_rua         = st.text_input("Rua / Avenida *",  value=s.f_end_rua,         key="w_rua")
        s.f_end_numero      = st.text_input("Número *",          value=s.f_end_numero,      key="w_num")
        s.f_end_complemento = st.text_input("Complemento",       value=s.f_end_complemento, key="w_comp")
        s.f_bairro          = st.text_input("Bairro *",          value=s.f_bairro,          key="w_bairro")
    with c2:
        s.f_cidade    = st.text_input("Cidade *", value=s.f_cidade, key="w_cidade")
        ufs = ["","AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS",
               "MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"]
        uf_idx        = ufs.index(s.f_estado_uf) if s.f_estado_uf in ufs else 0
        s.f_estado_uf = st.selectbox("Estado *", ufs, index=uf_idx, key="w_estado")
        s.f_cep       = st.text_input("CEP",      value=s.f_cep, key="w_cep")
    st.markdown('</div>', unsafe_allow_html=True)

    # PARTES ENVOLVIDAS
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("👥 Partes Envolvidas")
    c1, c2, c3 = st.columns(3)
    with c1: s.f_proprietario = st.text_input("Proprietário",                  value=s.f_proprietario, key="w_prop")
    with c2:
        lbl = "Inquilino / Locatário" if tipo_imovel == "Residencial" else "Empresa / Locatária"
        s.f_inquilino = st.text_input(lbl, value=s.f_inquilino, key="w_inq")
    with c3: s.f_corretor = st.text_input("Corretor Responsável *",            value=s.f_corretor,     key="w_corretor")
    st.markdown('</div>', unsafe_allow_html=True)

    # INFORMAÇÕES DA VISTORIA
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📅 Informações da Vistoria")
    c1, c2, c3 = st.columns(3)
    with c1:
        tvs   = ["Entrada","Saída","Periódica","Renovação"]
        tv_i  = tvs.index(s.f_tipo_vistoria) if s.f_tipo_vistoria in tvs else 0
        s.f_tipo_vistoria = st.selectbox("Tipo de Vistoria *", tvs, index=tv_i, key="w_tipov")
    with c2: s.f_data_vistoria = st.date_input("Data *",  value=s.f_data_vistoria, key="w_data")
    with c3: s.f_hora_vistoria = st.time_input("Hora *",  value=s.f_hora_vistoria, key="w_hora")
    st.markdown('</div>', unsafe_allow_html=True)

    # QUANTIDADES
    config         = get_config_imovel(tipo_imovel, subtipo)
    comodos_config = config["comodos"]
    icone_tipo     = config["icone"]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(f"{icone_tipo} Quantidades de Ambientes")
    st.caption("Altere os números — os campos de detalhe aparecem automaticamente.")
    if not s.f_qtd_comodos:
        s.f_qtd_comodos = {}
    cols_qtd = st.columns(3)
    for idx, (chave, label) in enumerate(comodos_config.items()):
        with cols_qtd[idx % 3]:
            val = int(s.f_qtd_comodos.get(chave, 0))
            s.f_qtd_comodos[chave] = st.number_input(label, min_value=0, max_value=20,
                                                      step=1, value=val, key=f"w_qtd_{chave}")
    st.markdown('</div>', unsafe_allow_html=True)

    # DETALHAMENTO POR AMBIENTE
    dados_comodos   = dict(s.f_dados_comodos) if s.f_dados_comodos else {}
    ativos = [c for c in comodos_config if s.f_qtd_comodos.get(c, 0) > 0]

    if ativos:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🔍 Detalhamento por Ambiente")
        for chave, label in comodos_config.items():
            qtd = int(s.f_qtd_comodos.get(chave, 0))
            if qtd == 0:
                continue
            label_s = label.rstrip('s') if label.endswith('s') and not label.endswith('ss') else label
            with st.expander(f"{icone_tipo} {label} ({qtd})", expanded=True):
                for i in range(qtd):
                    nome = f"{label_s} {i + 1}"
                    st.markdown(f"**{nome}**")
                    prev = dados_comodos.get(nome, {})
                    ce, co = st.columns([1, 2])
                    with ce:
                        opts  = ["Excelente","Bom","Regular","Ruim","Péssimo"]
                        e_idx = opts.index(prev.get('estado_geral','Bom')) if prev.get('estado_geral','Bom') in opts else 1
                        estado = st.selectbox("Estado Geral", opts, index=e_idx, key=f"w_est_{chave}_{i}")
                    with co:
                        obs = st.text_area("Observações", value=prev.get('observacoes',''),
                                           key=f"w_obs_{chave}_{i}", height=100,
                                           placeholder="Paredes, teto, piso, portas, janelas, danos...")
                    fotos_up = st.file_uploader(f"📷 Fotos — {nome}", type=["png","jpg","jpeg"],
                                                accept_multiple_files=True, key=f"w_fotos_{chave}_{i}")
                    fotos_salvas = prev.get('fotos', [])
                    fotos_novas  = []
                    if fotos_up:
                        for foto in fotos_up:
                            b = foto.read()
                            fotos_novas.append(f"data:image/{foto.type.split('/')[-1]};base64,{base64.b64encode(b).decode()}")
                        # Exibir preview em grade de 3 colunas
                        cols_foto = st.columns(3)
                        for fi, foto in enumerate(fotos_up):
                            foto.seek(0)
                            with cols_foto[fi % 3]:
                                st.image(foto.read(), caption=foto.name, use_column_width=True)
                    dados_comodos[nome] = {
                        "estado_geral": estado,
                        "observacoes":  obs,
                        "fotos":        fotos_novas if fotos_novas else fotos_salvas,
                    }
                    if i < qtd - 1:
                        st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)

    s.f_dados_comodos = dados_comodos

    # OBSERVAÇÕES FINAIS
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("📝 Observações Gerais")
    s.f_obs_gerais = st.text_area("Informações adicionais", value=s.f_obs_gerais,
                                  key="w_obs_gerais", height=150,
                                  placeholder="Condições gerais, acordos, pendências...")
    sts  = ["Concluída","Pendente","Problemas Identificados"]
    s_i  = sts.index(s.f_status) if s.f_status in sts else 0
    s.f_status = st.selectbox("Status da Vistoria", sts, index=s_i, key="w_status")
    st.markdown('</div>', unsafe_allow_html=True)

    return dados_comodos


# ================= MAIN =================

def main():
    init_db()
    init_session_state()

    # Header
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        try:
            st.image("logo01.png", use_column_width=True)
        except Exception:
            st.warning("⚠️ Adicione logo01.png na raiz do repositório.")
        st.markdown("""
            <div style="text-align:center;background:white;padding:1rem;border-radius:12px;
                        box-shadow:0 4px 6px rgba(0,0,0,0.1);margin-bottom:2rem;">
                <div style="font-size:1.8rem;font-weight:700;color:#1a2b4a;margin-top:0.5rem;">
                    Laudo de Vistoria</div>
                <div style="font-size:1rem;color:#64748b;margin-top:0.4rem;">
                    Sistema Profissional de Gestão de Vistorias Imobiliárias</div>
            </div>""", unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Estatísticas")
        df_all   = get_vistorias()
        df_rascs = get_rascunhos()
        c1, c2   = st.columns(2)
        with c1: st.metric("Total", len(df_all))
        with c2: st.metric("Concluídas", len(df_all[df_all['status']=='Concluída']) if not df_all.empty else 0)
        if not df_rascs.empty:
            st.warning(f"📝 {len(df_rascs)} rascunho(s) não finalizado(s)")
        st.markdown("---")
        st.markdown("""
        ### 💡 Dicas
        - 💾 Rascunhos salvos automaticamente
        - ▶️ Retome de onde parou
        - 📸 Fotos são preservadas
        - ✅ Finalize para gerar PDF
        """)

    tab1, tab2, tab3 = st.tabs(["📝 Nova Vistoria", "📋 Minhas Vistorias", "ℹ️ Ajuda"])

    # ====== TAB 1 ======
    with tab1:

        # Limpar flag de redirecionamento (chegou aqui, pode apagar)
        if st.session_state.ir_para_tab1:
            st.session_state.ir_para_tab1 = False

        # Tela de sucesso
        if st.session_state.vistoria_finalizada:
            st.success("✅ Vistoria salva com sucesso! Acesse 'Minhas Vistorias' para gerar o PDF.")
            if st.button("➕ Nova Vistoria", key="btn_nova"):
                st.session_state.vistoria_finalizada = False
                limpar_formulario()
                st.rerun()
            st.stop()

        # Banner: modo edição de vistoria concluída
        if st.session_state.modo_edicao and st.session_state.rascunho_id:
            st.markdown(f"""
                <div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;
                            border-radius:12px;padding:1rem 1.5rem;margin-bottom:1rem;">
                    ✏️ <b>Modo Edição</b> — Vistoria ID {st.session_state.rascunho_id} carregada.<br>
                    <span style="font-size:0.9rem;color:#1e40af;">
                    Faça as alterações desejadas e clique em <b>✅ Salvar Alterações</b> quando terminar.
                    </span>
                </div>""", unsafe_allow_html=True)

        # Banner: rascunho em andamento (nova vistoria)
        elif st.session_state.rascunho_id:
            ts = st.session_state.ultimo_auto_save
            ts_str = ts.strftime('%H:%M:%S') if ts else "—"
            st.markdown(f"""
                <div class="salvo-banner">
                    💾 Rascunho salvo automaticamente às <b>{ts_str}</b> — seus dados estão seguros.
                </div>""", unsafe_allow_html=True)

        else:
            # Banner: há rascunhos para retomar
            df_r = get_rascunhos()
            if not df_r.empty:
                st.markdown('<div class="rascunho-banner">', unsafe_allow_html=True)
                st.markdown("### ⚠️ Você tem vistorias não finalizadas!")
                for _, r in df_r.iterrows():
                    end_r = str(r['endereco'])[:60] + "..." if len(str(r['endereco'])) > 60 else r['endereco']
                    ca, cb = st.columns([3, 1])
                    with ca:
                        data_mod = str(r['data_modificacao'])[:16]
                        # Converter "YYYY-MM-DD HH:MM" para "DD/MM/YYYY HH:MM"
                        try:
                            data_mod = datetime.strptime(data_mod, '%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M')
                        except Exception:
                            pass
                        st.markdown(f"**ID {r['id']}** — {end_r}  \n🕐 {data_mod}")
                    with cb:
                        if st.button("▶️ Continuar", key=f"cont_{r['id']}"):
                            limpar_formulario()
                            carregar_rascunho_no_estado(int(r['id']))
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Formulário principal
        dados_comodos = renderizar_formulario()

        # Auto-save a cada interação
        auto_salvar(dados_comodos)

        # Botões
        st.markdown("---")
        cb1, cb2, cb3 = st.columns(3)

        with cb1:
            # No modo edição, não faz sentido salvar como rascunho
            if not st.session_state.modo_edicao:
                if st.button("💾 Salvar Rascunho Agora", use_container_width=True):
                    dados = montar_dados(dados_comodos, status_override='Rascunho')
                    novo_id = salvar_vistoria(dados, vistoria_id=st.session_state.rascunho_id)
                    st.session_state.rascunho_id      = novo_id
                    st.session_state.ultimo_auto_save = datetime.now()
                    st.success(f"💾 Rascunho salvo! (ID {novo_id})")

        with cb2:
            btn_finalizar = "✅ Salvar Alterações" if st.session_state.modo_edicao else "✅ Finalizar Vistoria"
            if st.button(btn_finalizar, use_container_width=True, type="primary"):
                # Em modo edição, manter o status original (não mudar para o que está no selectbox)
                status_final = st.session_state.status_original if st.session_state.modo_edicao else None
                dados = montar_dados(dados_comodos, status_override=status_final)
                erros = validar_dados(dados)
                if erros:
                    for e in erros:
                        st.error(f"❌ {e}")
                else:
                    salvar_vistoria(dados, vistoria_id=st.session_state.rascunho_id)
                    st.session_state.vistoria_finalizada = True
                    st.session_state.rascunho_id  = None
                    st.session_state.modo_edicao  = False
                    st.session_state.status_original = None
                    st.balloons()
                    st.rerun()

        with cb3:
            btn_cancelar = "❌ Cancelar Edição" if st.session_state.modo_edicao else "🗑️ Descartar Rascunho"
            if st.button(btn_cancelar, use_container_width=True):
                # No modo edição, apenas limpa o formulário SEM deletar a vistoria original
                if not st.session_state.modo_edicao and st.session_state.rascunho_id:
                    deletar_vistoria(st.session_state.rascunho_id)
                limpar_formulario()
                st.rerun()

    # ====== TAB 2 ======
    with tab2:

        # Aviso de redirecionamento quando acabou de clicar em Editar
        if st.session_state.modo_edicao and st.session_state.rascunho_id:
            st.success(f"✅ Vistoria ID {st.session_state.rascunho_id} carregada! "
                       f"Clique na aba **📝 Nova Vistoria** para editar.")

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📋 Vistorias Cadastradas")
        cf1, cf2, cf3 = st.columns([2,1,1])
        with cf1: busca        = st.text_input("🔍 Buscar", placeholder="Endereço, proprietário ou inquilino...")
        with cf2: filtro_status = st.selectbox("Status", ["Todos","Concluída","Pendente","Problemas Identificados","Rascunho"])
        with cf3: filtro_tipo   = st.selectbox("Tipo",   ["Todos","Entrada","Saída","Periódica","Renovação"])
        st.markdown('</div>', unsafe_allow_html=True)

        df = get_vistorias(
            filtro_status=filtro_status if filtro_status != "Todos" else None,
            filtro_tipo=filtro_tipo   if filtro_tipo   != "Todos" else None,
            busca=busca if busca else None
        )

        if df.empty:
            st.info("📭 Nenhuma vistoria encontrada.")
        else:
            cs1,cs2,cs3,cs4,cs5 = st.columns(5)
            with cs1: st.metric("Total",      len(df))
            with cs2: st.metric("Concluídas", len(df[df['status']=='Concluída']))
            with cs3: st.metric("Pendentes",  len(df[df['status']=='Pendente']))
            with cs4: st.metric("Problemas",  len(df[df['status']=='Problemas Identificados']))
            with cs5: st.metric("Rascunhos",  len(df[df['status']=='Rascunho']))

            st.markdown("---")
            st.dataframe(df, use_container_width=True, hide_index=True,
                column_config={
                    "id":                st.column_config.NumberColumn("ID",        width="small"),
                    "tipo_imovel":       st.column_config.TextColumn("Categoria",   width="small"),
                    "subtipo_comercial": st.column_config.TextColumn("Subtipo",     width="medium"),
                    "endereco":          st.column_config.TextColumn("Endereço",    width="large"),
                    "proprietario":      st.column_config.TextColumn("Proprietário",width="medium"),
                    "inquilino":         st.column_config.TextColumn("Inquilino",   width="medium"),
                    "tipo_vistoria":     st.column_config.TextColumn("Tipo",        width="small"),
                    "data_vistoria":     st.column_config.DateColumn("Data", width="small", format="DD/MM/YYYY"),
                    "status":            st.column_config.TextColumn("Status",      width="medium"),
                })

            st.markdown("---")
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("⚙️ Ações")
            ca1, ca2 = st.columns(2)
            with ca1:
                vid = st.selectbox("Selecionar Vistoria", df['id'].tolist(),
                    format_func=lambda x: f"ID {x} — {df[df['id']==x]['endereco'].values[0][:50]}...")
                row_sel    = df[df['id'] == vid]
                status_sel = row_sel['status'].values[0] if not row_sel.empty else ''
                if status_sel == 'Rascunho':
                    st.warning("⚠️ Rascunho não finalizado.")
                else:
                    st.info(f"Status atual: **{status_sel}**")

            with ca2:
                st.write(""); st.write("")
                cb1, cb2, cb3, cb4 = st.columns(4)
                with cb1:
                    btn_label = "▶️ Continuar" if status_sel == 'Rascunho' else "✏️ Editar"
                    if st.button(btn_label, use_container_width=True, key="btn_editar"):
                        limpar_formulario()
                        carregar_rascunho_no_estado(int(vid))
                        st.session_state.vistoria_finalizada = False
                        st.session_state.modo_edicao         = (status_sel != 'Rascunho')
                        st.session_state.status_original     = status_sel
                        st.session_state.ir_para_tab1        = True
                        # Não marca auto_save ainda para não sobrescrever status
                        st.session_state.ultimo_auto_save    = None
                        st.rerun()
                with cb2:
                    if st.button("📄 PDF", use_container_width=True):
                        row = get_vistoria_by_id(int(vid))
                        if row:
                            with st.spinner("Gerando PDF..."):
                                try:
                                    pdf = gerar_pdf_profissional(row)
                                    st.download_button("⬇️ Baixar PDF", data=pdf,
                                        file_name=f"vistoria_{vid}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf", use_container_width=True)
                                except Exception as e:
                                    st.error(f"Erro: {e}")
                with cb3:
                    if st.button("📊 Excel", use_container_width=True):
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine='openpyxl') as w:
                            df.to_excel(w, index=False, sheet_name='Vistorias')
                        buf.seek(0)
                        st.download_button("⬇️ Excel", data=buf,
                            file_name=f"vistorias_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
                with cb4:
                    if st.button("🗑️ Excluir", type="secondary", use_container_width=True):
                        if st.checkbox(f"Confirmar exclusão {vid}?"):
                            deletar_vistoria(int(vid))
                            st.success("✅ Excluída!")
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # ====== TAB 3 ======
    with tab3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("💡 Como Usar o Sistema")
        st.markdown("""
        ### 💾 Sistema de Rascunho Automático
        | Situação | O que acontece |
        |----------|---------------|
        | Você começa a preencher | Rascunho criado automaticamente |
        | App reinicia ou cai | Dados preservados no banco |
        | Você reabre o app | Banner amarelo aparece com botão ▶️ Continuar |
        | Você termina | Clica em ✅ Finalizar Vistoria |

        ### 🎯 Fluxo de Vistoria
        1. Escolha o **tipo de imóvel** (Residencial ou Comercial)
        2. Preencha os **dados e as partes**
        3. Informe as **quantidades** de cada ambiente
        4. Detalhe com **estado, observações e fotos**
        5. Clique em **✅ Finalizar Vistoria**
        6. Gere o **Laudo em PDF** na aba Minhas Vistorias

        ### 🏷️ Tipos de Imóvel
        | Categoria | Subtipos disponíveis |
        |-----------|---------------------|
        | 🏠 Residencial | Quartos, Sala, Cozinha, Banheiro… |
        | 🏢 Comercial | Sala Comercial, Ponto Comercial, Loja, Galpão, Escritório, Consultório, Restaurante/Bar, Clínica/Lab, Outro |

        ### 💡 Dicas
        - Campos com quantidade **0** não aparecem no formulário nem no PDF
        - O PDF inclui até **9 fotos por ambiente** (3 por linha)
        - Use **💾 Salvar Rascunho Agora** antes de sair se quiser garantir o salvamento
        - Na aba Minhas Vistorias filtre por **Rascunho** para ver pendências
        - O botão **✏️ Editar** funciona para qualquer vistoria, mesmo as já concluídas
        """)
        st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
