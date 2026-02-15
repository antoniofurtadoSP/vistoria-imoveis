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
        
        .stTabs [data-baseweb="tab"] {
            padding: 0 12px;
            font-size: 0.9rem;
        }
    }
    
    /* Animações suaves */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stMarkdown, .stDataFrame {
        animation: fadeIn 0.5s ease-in;
    }
</style>
""", unsafe_allow_html=True)

# ================= BANCO DE DADOS =================

def inicializar_bd():
    """Cria a tabela de vistorias se não existir"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vistorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endereco TEXT NOT NULL,
        proprietario TEXT,
        inquilino TEXT,
        corretor_responsavel TEXT,
        tipo_vistoria TEXT,
        data_vistoria DATE,
        hora_vistoria TIME,
        quartos INTEGER,
        banheiros INTEGER,
        salas INTEGER,
        cozinhas INTEGER,
        areas_servico INTEGER,
        vagas_garagem INTEGER,
        dados_comodos TEXT,
        observacoes_gerais TEXT,
        status TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def salvar_vistoria(dados):
    """Salva uma nova vistoria no banco"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO vistorias (
        endereco, proprietario, inquilino, corretor_responsavel,
        tipo_vistoria, data_vistoria, hora_vistoria,
        quartos, banheiros, salas, cozinhas, areas_servico, vagas_garagem,
        dados_comodos, observacoes_gerais, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
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

def get_vistorias(filtro_status=None, filtro_tipo=None, busca=None):
    """Recupera vistorias com filtros opcionais"""
    conn = sqlite3.connect(DB_NAME)
    
    query = "SELECT id, endereco, proprietario, inquilino, tipo_vistoria, data_vistoria, status FROM vistorias WHERE 1=1"
    params = []
    
    if filtro_status:
        query += " AND status = ?"
        params.append(filtro_status)
    
    if filtro_tipo:
        query += " AND tipo_vistoria = ?"
        params.append(filtro_tipo)
    
    if busca:
        query += " AND (endereco LIKE ? OR proprietario LIKE ? OR inquilino LIKE ?)"
        busca_param = f"%{busca}%"
        params.extend([busca_param, busca_param, busca_param])
    
    query += " ORDER BY criado_em DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def get_vistoria_by_id(vistoria_id):
    """Recupera uma vistoria específica pelo ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM vistorias WHERE id = ?", (vistoria_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))
    return None

def deletar_vistoria(vistoria_id):
    """Deleta uma vistoria pelo ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM vistorias WHERE id = ?", (vistoria_id,))
    
    conn.commit()
    conn.close()

# ================= VALIDAÇÃO =================

def validar_dados(dados):
    """Valida os dados antes de salvar"""
    erros = []
    
    if not dados.get('endereco'):
        erros.append("Endereço é obrigatório")
    
    if not dados.get('tipo_vistoria'):
        erros.append("Tipo de vistoria é obrigatório")
    
    if not dados.get('data_vistoria'):
        erros.append("Data da vistoria é obrigatória")
    
    return erros

# ================= GERAÇÃO DE PDF =================

def gerar_pdf_profissional(vistoria):
    """Gera um PDF profissional da vistoria"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilo customizado para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a2b4a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulo
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#C9A961'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para seções
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a2b4a'),
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor('#C9A961'),
        borderPadding=5
    )
    
    # Título principal
    story.append(Paragraph("LAUDO DE VISTORIA", title_style))
    story.append(Paragraph(f"ID: {vistoria['id']}", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Informações básicas
    story.append(Paragraph("Informações Gerais", section_style))
    
    info_data = [
        ["Endereço:", vistoria['endereco']],
        ["Proprietário:", vistoria['proprietario'] or "-"],
        ["Inquilino:", vistoria['inquilino'] or "-"],
        ["Corretor:", vistoria['corretor_responsavel'] or "-"],
        ["Tipo:", vistoria['tipo_vistoria']],
        ["Data:", vistoria['data_vistoria']],
        ["Horário:", vistoria['hora_vistoria'] or "-"],
        ["Status:", vistoria['status']],
    ]
    
    info_table = Table(info_data, colWidths=[120, 370])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a2b4a')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Características do imóvel
    story.append(Paragraph("Características do Imóvel", section_style))
    
    caract_data = [
        ["Quartos:", str(vistoria['quartos'])],
        ["Banheiros:", str(vistoria['banheiros'])],
        ["Salas:", str(vistoria['salas'])],
        ["Cozinhas:", str(vistoria['cozinhas'])],
        ["Áreas de Serviço:", str(vistoria['areas_servico'])],
        ["Vagas de Garagem:", str(vistoria['vagas_garagem'])],
    ]
    
    caract_table = Table(caract_data, colWidths=[180, 310])
    caract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a2b4a')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(caract_table)
    story.append(Spacer(1, 20))
    
    # Detalhes dos cômodos
    if vistoria['dados_comodos']:
        story.append(PageBreak())
        story.append(Paragraph("Detalhes dos Cômodos", section_style))
        
        try:
            dados_comodos = json.loads(vistoria['dados_comodos'])
            
            for tipo_comodo, comodos in dados_comodos.items():
                if comodos:
                    story.append(Paragraph(f"<b>{tipo_comodo.upper()}</b>", styles['Heading3']))
                    story.append(Spacer(1, 10))
                    
                    for idx, comodo in enumerate(comodos, 1):
                        comodo_data = [
                            [f"{tipo_comodo} {idx}", ""],
                            ["Estado:", comodo.get('estado', '-')],
                            ["Observações:", comodo.get('observacoes', '-')],
                        ]
                        
                        comodo_table = Table(comodo_data, colWidths=[120, 370])
                        comodo_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2b4a')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8fafc')),
                            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1a2b4a')),
                            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                            ('PADDING', (0, 0), (-1, -1), 8),
                        ]))
                        
                        story.append(comodo_table)
                        story.append(Spacer(1, 15))
                        
                        # Fotos (se houver)
                        fotos = comodo.get('fotos', [])
                        if fotos:
                            for foto in fotos:
                                try:
                                    img_data = base64.b64decode(foto.split(',')[1] if ',' in foto else foto)
                                    img = PilImage.open(io.BytesIO(img_data))
                                    
                                    # Redimensionar imagem se necessário
                                    max_width = 400
                                    if img.width > max_width:
                                        ratio = max_width / img.width
                                        new_height = int(img.height * ratio)
                                        img = img.resize((max_width, new_height))
                                    
                                    # Salvar imagem em buffer
                                    img_buffer = io.BytesIO()
                                    img.save(img_buffer, format='PNG')
                                    img_buffer.seek(0)
                                    
                                    # Adicionar ao PDF
                                    rl_img = RLImage(img_buffer, width=img.width, height=img.height)
                                    story.append(rl_img)
                                    story.append(Spacer(1, 10))
                                except Exception as e:
                                    print(f"Erro ao processar foto: {e}")
        
        except json.JSONDecodeError:
            story.append(Paragraph("Erro ao carregar detalhes dos cômodos", styles['Normal']))
    
    # Observações gerais
    if vistoria['observacoes_gerais']:
        story.append(PageBreak())
        story.append(Paragraph("Observações Gerais", section_style))
        obs_style = ParagraphStyle(
            'Obs',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )
        story.append(Paragraph(vistoria['observacoes_gerais'].replace('\n', '<br/>'), obs_style))
    
    # Rodapé
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}", footer_style))
    story.append(Paragraph("Sistema de Vistoria de Imóveis - AF Imóveis", footer_style))
    
    # Construir PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()

# ================= INTERFACE PRINCIPAL =================

def main():
    """Função principal do aplicativo"""
    
    # Inicializar banco de dados
    inicializar_bd()
    
    # Header com logo usando texto estilizado ao invés de imagem
    st.markdown('''
        <div class="header-container">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🏠</div>
            <div class="app-title">AF Imóveis</div>
            <div class="app-subtitle">Sistema Profissional de Vistoria de Imóveis</div>
            <div style="margin-top: 1rem; color: #64748b; font-size: 0.9rem;">
                📱 Compatível com Mobile | 💾 Sincronização em Nuvem | 📄 Laudos Profissionais
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    # Tabs principais
    tab1, tab2, tab3 = st.tabs(["📝 Nova Vistoria", "📋 Vistorias", "💡 Ajuda"])
    
    # ========== TAB 1: NOVA VISTORIA ==========
    with tab1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🏗️ Cadastrar Nova Vistoria")
        
        with st.form("form_vistoria", clear_on_submit=False):
            st.markdown("### 📍 Informações do Imóvel")
            
            # Dados do endereço
            col1, col2 = st.columns([3, 1])
            with col1:
                endereco_rua = st.text_input("* Rua/Avenida", placeholder="Ex: Rua das Flores")
            with col2:
                endereco_numero = st.text_input("* Número", placeholder="123")
            
            col3, col4 = st.columns(2)
            with col3:
                endereco_complemento = st.text_input("Complemento", placeholder="Apto 45, Bloco B")
            with col4:
                bairro = st.text_input("* Bairro", placeholder="Centro")
            
            col5, col6, col7 = st.columns([2, 1, 1])
            with col5:
                cidade = st.text_input("* Cidade", placeholder="São Paulo")
            with col6:
                estado = st.selectbox("* Estado", [
                    "SP", "RJ", "MG", "ES", "PR", "SC", "RS", "BA", "SE", "AL", 
                    "PE", "PB", "RN", "CE", "PI", "MA", "PA", "AP", "AM", "RR", 
                    "AC", "RO", "MT", "MS", "GO", "TO", "DF"
                ])
            with col7:
                cep = st.text_input("CEP", placeholder="01234-567")
            
            st.markdown("---")
            st.markdown("### 👥 Informações das Partes")
            
            col8, col9 = st.columns(2)
            with col8:
                proprietario = st.text_input("Proprietário", placeholder="Nome do proprietário")
                corretor_responsavel = st.text_input("Corretor Responsável", placeholder="Nome do corretor")
            with col9:
                inquilino = st.text_input("Inquilino", placeholder="Nome do inquilino (se aplicável)")
                tipo_vistoria = st.selectbox(
                    "* Tipo de Vistoria",
                    ["Entrada", "Saída", "Periódica", "Renovação"],
                    help="Selecione o tipo de vistoria sendo realizada"
                )
            
            st.markdown("---")
            st.markdown("### 📅 Data e Horário")
            
            col10, col11 = st.columns(2)
            with col10:
                data_vistoria = st.date_input(
                    "* Data da Vistoria",
                    value=datetime.now(),
                    help="Data em que a vistoria está sendo realizada"
                )
            with col11:
                hora_vistoria = st.time_input(
                    "Horário da Vistoria",
                    value=datetime.now().time(),
                    help="Horário de início da vistoria"
                )
            
            st.markdown("---")
            st.markdown("### 🏘️ Características do Imóvel")
            
            col12, col13, col14 = st.columns(3)
            with col12:
                quartos = st.number_input("Quartos", min_value=0, value=2, step=1)
                banheiros = st.number_input("Banheiros", min_value=0, value=1, step=1)
            with col13:
                salas = st.number_input("Salas", min_value=0, value=1, step=1)
                cozinhas = st.number_input("Cozinhas", min_value=0, value=1, step=1)
            with col14:
                areas_servico = st.number_input("Áreas de Serviço", min_value=0, value=1, step=1)
                vagas_garagem = st.number_input("Vagas de Garagem", min_value=0, value=0, step=1)
            
            st.markdown("---")
            st.markdown("### 📸 Detalhamento por Cômodo")
            
            # Estrutura para armazenar dados dos cômodos
            dados_comodos = {}
            tipos_comodos = {
                'quartos': int(quartos),
                'banheiros': int(banheiros),
                'salas': int(salas),
                'cozinhas': int(cozinhas),
                'areas_servico': int(areas_servico)
            }
            
            for tipo, quantidade in tipos_comodos.items():
                if quantidade > 0:
                    tipo_label = tipo.replace('_', ' ').title()
                    
                    with st.expander(f"📋 {tipo_label} ({quantidade})", expanded=False):
                        comodos_lista = []
                        
                        for i in range(quantidade):
                            st.markdown(f"**{tipo_label[:-1] if tipo_label.endswith('s') else tipo_label} {i+1}**")
                            
                            col_estado, col_obs = st.columns([1, 2])
                            
                            with col_estado:
                                estado_comodo = st.selectbox(
                                    "Estado",
                                    ["Excelente", "Bom", "Regular", "Ruim", "Péssimo"],
                                    key=f"estado_{tipo}_{i}",
                                    help="Condição geral do cômodo"
                                )
                            
                            with col_obs:
                                obs_comodo = st.text_area(
                                    "Observações",
                                    key=f"obs_{tipo}_{i}",
                                    height=100,
                                    placeholder="Descreva detalhes importantes: danos, manchas, condição de pisos, paredes, etc."
                                )
                            
                            # Upload de fotos
                            fotos = st.file_uploader(
                                f"📷 Fotos do {tipo_label[:-1] if tipo_label.endswith('s') else tipo_label} {i+1}",
                                type=['png', 'jpg', 'jpeg'],
                                accept_multiple_files=True,
                                key=f"fotos_{tipo}_{i}",
                                help="Tire fotos de diferentes ângulos do cômodo"
                            )
                            
                            # Processar fotos para base64
                            fotos_base64 = []
                            if fotos:
                                for foto in fotos:
                                    img_bytes = foto.read()
                                    img_base64 = base64.b64encode(img_bytes).decode()
                                    fotos_base64.append(f"data:image/{foto.type.split('/')[-1]};base64,{img_base64}")
                                    
                                    # Preview das fotos
                                    st.image(img_bytes, caption=foto.name, width=200)
                            
                            comodos_lista.append({
                                'estado': estado_comodo,
                                'observacoes': obs_comodo,
                                'fotos': fotos_base64
                            })
                            
                            st.markdown("---")
                        
                        dados_comodos[tipo] = comodos_lista
            
            st.markdown("---")
            st.markdown("### 📝 Observações Gerais")
            
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            
            observacoes_gerais = st.text_area(
                "Observações Gerais da Vistoria",
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
