
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from reportlab.lib.colors import HexColor
import re
import logging
from typing import Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFConverter:
    """Classe pour convertir automatiquement les scénarios en PDF"""
    
    def __init__(self):
        """Initialiser le convertisseur PDF"""
        self.setup_fonts()
        self.setup_styles()
        
    def setup_fonts(self):
        """Configurer les polices pour le PDF"""
        try:
            # Utiliser des polices système ou par défaut
            self.title_font = "Helvetica-Bold"
            self.body_font = "Helvetica"
            self.arabic_font = "Helvetica"  # Fallback pour l'arabe
            logger.info("[OK] Polices configurees")
        except Exception as e:
            logger.warning(f"[ATTENTION] Erreur configuration polices: {e}")
            self.title_font = "Helvetica-Bold"
            self.body_font = "Helvetica"
            self.arabic_font = "Helvetica"
    
    def setup_styles(self):
        """Configurer les styles pour le PDF"""
        self.styles = getSampleStyleSheet()
        
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=HexColor('#1e3c72'),
            spaceAfter=30,
            alignment=1,  # Center
            fontName=self.title_font
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#2a5298'),
            spaceAfter=12,
            spaceBefore=20,
            fontName=self.title_font
        ))
        
        # Style pour le corps du texte
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=4,
            leading=16,
            fontName=self.body_font,
            alignment=4  # Justify
        ))
        
        # Style pour les éléments en gras
        self.styles.add(ParagraphStyle(
            name='CustomBold',
            parent=self.styles['CustomBody'],
            fontSize=12,
            fontName=self.title_font,
            textColor=HexColor('#1e3c72')
        ))
        
        # Style pour l'en-tête
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=HexColor('#666666'),
            alignment=1,
            spaceAfter=20
        ))
        
        # Style pour le pied de page
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=HexColor('#888888'),
            alignment=1
        ))
    
    def clean_text_for_pdf(self, text: str) -> str:
        """Nettoyer le texte pour l'affichage PDF"""
        # Supprimer les emojis problématiques pour ReportLab
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u"\U00002700-\U000027BF"  # dingbats
                                   u"\U0001f926-\U0001f937"
                                   u"\U00010000-\U0010ffff"
                                   u"\u2600-\u2B55"
                                   u"\u200d"
                                   u"\u23cf"
                                   u"\u23e9"
                                   u"\u231a"
                                   u"\ufe0f"
                                   u"\u3030"
                                   "]+", flags=re.UNICODE)
        
        # Remplacer les emojis par des équivalents texte
        emoji_replacements = {
            "🏺": "[TRESOR]",
            "🗡️": "[EPEE]", 
            "⚔️": "[COMBAT]",
            "🏰": "[PALAIS]",
            "🕌": "[MOSQUEE]",
            "📜": "[PARCHEMIN]",
            "🌟": "[ETOILE]",
            "🔍": "[RECHERCHE]",
            "💎": "[GEMME]",
            "🏛️": "[EDIFICE]",
            "🌙": "[LUNE]",
            "☀️": "[SOLEIL]",
            "🎭": "[MASQUE]",
            "📚": "[LIVRES]",
            "🎯": "[OBJECTIF]",
            "🔥": "[FEU]",
            "💫": "[MAGIE]",
            "🗝️": "[CLE]",
        }
        
        clean_text = text
        for emoji, replacement in emoji_replacements.items():
            clean_text = clean_text.replace(emoji, replacement)
        
        # Supprimer les emojis restants
        clean_text = emoji_pattern.sub('', clean_text)
        
        # Nettoyer les caractères problématiques
        clean_text = clean_text.replace('«', '"').replace('»', '"')
        clean_text = clean_text.replace(''', "'").replace(''', "'")
        clean_text = clean_text.replace('"', '"').replace('"', '"')
        clean_text = clean_text.replace('–', '-').replace('—', '-')
        
        return clean_text
    
    def parse_markdown_to_elements(self, content: str) -> list:
        """Parser le contenu markdown et créer des éléments PDF"""
        elements = []
        content = self.clean_text_for_pdf(content)
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # Titre principal (# )
            if line.startswith('# '):
                title = line[2:].strip()
                elements.append(Paragraph(title, self.styles['CustomTitle']))
                elements.append(Spacer(1, 12))
            
            # Sous-titre (## )
            elif line.startswith('## '):
                subtitle = line[3:].strip()
                elements.append(Paragraph(subtitle, self.styles['CustomHeading']))
            
            # Sous-sous-titre (### )
            elif line.startswith('### '):
                subsubtitle = line[4:].strip()
                para = Paragraph(f"<b>{subsubtitle}</b>", self.styles['CustomBold'])
                elements.append(para)
            
            # Liste à puces
            elif line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()
                para = Paragraph(f"• {bullet_text}", self.styles['CustomBody'])
                elements.append(para)
            
            # Texte en gras (**text**)
            elif '**' in line:
                # Traiter le markdown gras
                processed = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                para = Paragraph(processed, self.styles['CustomBody'])
                elements.append(para)
            
            # Paragraphe normal
            else:
                if line:
                    para = Paragraph(line, self.styles['CustomBody'])
                    elements.append(para)
            
            i += 1
        
        return elements
    
    def create_header_footer(self, canvas, doc, title: str):
        """Créer l'en-tête et le pied de page"""
        canvas.saveState()
        
        # En-tête
        header_text = f"SIFHR - Scénarios de Chasse au Trésor Arabo-Musulmans"
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(HexColor('#666666'))
        canvas.drawCentredText(A4[0]/2, A4[1]-30, header_text)
        
        # Ligne de séparation
        canvas.setStrokeColor(HexColor('#4682b4'))
        canvas.setLineWidth(1)
        canvas.line(50, A4[1]-45, A4[0]-50, A4[1]-45)
        
        # Pied de page
        footer_text = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | Page {canvas.getPageNumber()}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(HexColor('#888888'))
        canvas.drawCentredText(A4[0]/2, 30, footer_text)
        
        # Signature SIFHR
        canvas.drawCentredText(A4[0]/2, 15, "Système Immersif de Fiction Historique Riche © 2024")
        
        canvas.restoreState()
    
    def convert_to_pdf(self, scenario_content: str, scenario_title: str) -> Tuple[bytes, str]:
        """Convertir un scénario en PDF et retourner les bytes + nom de fichier"""
        try:
            logger.info(f"🔄 Conversion PDF démarrée pour: {scenario_title}")
            
            # Créer un buffer en mémoire
            buffer = BytesIO()
            
            # Créer le document PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=60,
                leftMargin=60,
                topMargin=60,
                bottomMargin=60,
                title=scenario_title
            )
            
            # Parser le contenu markdown
            elements = self.parse_markdown_to_elements(scenario_content)
            
            # Ajouter l'en-tête du document
            header_para = Paragraph(
                f"Généré le {datetime.now().strftime('%d %B %Y')}",
                self.styles['Header']
            )
            elements.insert(0, header_para)
            
            # Fonction pour l'en-tête/pied de page
            def add_page_elements(canvas, doc):
                self.create_header_footer(canvas, doc, scenario_title)
            
            # Construire le PDF
            doc.build(elements, onFirstPage=add_page_elements, onLaterPages=add_page_elements)
            
            # Récupérer les bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Générer le nom de fichier
            safe_title = re.sub(r'[^\w\s-]', '', scenario_title)
            safe_title = re.sub(r'[-\s]+', '-', safe_title)[:50]
            filename = f"SIFHR_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            logger.info(f"[OK] PDF genere avec succes: {len(pdf_bytes)} bytes")
            
            return pdf_bytes, filename
            
        except Exception as e:
            logger.error(f"[ERREUR] Erreur lors de la conversion PDF: {e}")
            raise Exception(f"Erreur de conversion PDF: {str(e)}")

# Instance globale
pdf_converter = PDFConverter()