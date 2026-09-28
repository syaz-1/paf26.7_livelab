#!/usr/bin/env python3
"""Export the LiveLab and its appendices to DOCX using standard-library OOXML."""
from pathlib import Path
import re
import argparse
import zipfile
import struct
from xml.sax.saxutils import escape, quoteattr
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--paf-only', action='store_true', help='Export the UI-only workshop with a prepared database')
parser.add_argument('--private-evidence', action='store_true', help='PAF-only: include local live-answer screenshots and write only under ignored .local/')
args = parser.parse_args()
if args.private_evidence and not args.paf_only:
    parser.error('--private-evidence requires --paf-only')
LAB = ROOT / ('docs/livelab-paf-only' if args.paf_only else 'docs/livelab')
OUT = LAB / ('ADB_Health_Monitoring_Agent_PAF_Only_LiveLab.docx' if args.paf_only else 'ADB_Health_Monitoring_Agent_LiveLab.docx')
PRIVATE = ROOT / '.local/paf-screenshots'
if args.private_evidence:
    OUT = PRIVATE / 'ADB_Health_Monitoring_Agent_PAF_Only_LiveLab_PRIVATE.docx'
APPENDICES = ([('A','Complete Agent instructions','monitoring-agent-instructions.txt'), ('B','Validation prompts','test-prompts.md')]
              if args.paf_only else [('A','Database preparation SQL','prepare-monitoring.sql'),('B','Runtime verification SQL','verify-monitoring.sql'),('C','Complete Agent instructions','monitoring-agent-instructions.txt'),('D','Validation prompts','test-prompts.md')])
NAVIGATION = (['Confirm the prepared environment','Configure the PAF database connection','Configure the Agent model','Configure the Select AI profile','Build the custom Agent flow','Test the flow in Playground','Save, troubleshoot and hand over']
              if args.paf_only else ['Prepare the environment','Prepare monitoring views','Configure connections','Configure Select AI','Build the Agent','Test in Playground','Troubleshoot and hand over'])
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
relationships = []
images = []
bookmark_number = 0
anchors = {'files/'+file:'appendix_'+letter.lower() for letter, title, file in APPENDICES}


def run(text, bold=False, code=False):
    props = ('<w:b/>' if bold else '')
    if code:
        props += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/>'
    return '<w:r><w:rPr>' + props + '</w:rPr><w:t xml:space="preserve">' + escape(text) + '</w:t></w:r>'


def inline(text):
    parts=[]; end=0
    pattern=r'\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`'
    for m in re.finditer(pattern,text):
        parts.append(run(text[end:m.start()]))
        if m.group(1) is not None:
            label,url=m.group(1),m.group(2)
            if url in anchors:
                parts.append('<w:hyperlink w:anchor="'+anchors[url]+'">'+run(label)+' </w:hyperlink>')
            elif url.startswith(('https://','http://')):
                rid='rIdLink'+str(len(relationships)+1);relationships.append((rid,url))
                parts.append('<w:hyperlink r:id="'+rid+'">'+run(label)+'</w:hyperlink>')
            else:
                parts.append(run(label+' [repository reference: '+url+']'))
        elif m.group(3) is not None:parts.append(run(m.group(3),bold=True))
        else:parts.append(run(m.group(4),code=True))
        end=m.end()
    parts.append(run(text[end:]))
    return ''.join(parts)


def paragraph(text='',style=None,bookmark=None,page_break=False):
    global bookmark_number
    props=('<w:pStyle w:val="'+style+'"/>' if style else '')
    if page_break:props+='<w:pageBreakBefore/>'
    content=inline(text) if style!='Code' else run(text,code=True)
    if bookmark:
        bookmark_number+=1
        content=f'<w:bookmarkStart w:id="{bookmark_number}" w:name="{bookmark}"/>'+content+f'<w:bookmarkEnd w:id="{bookmark_number}"/>'
    return '<w:p><w:pPr>'+props+'</w:pPr>'+content+'</w:p>'


def table(rows):
    cols=len(rows[0]);widths=([3600,6400] if cols==2 else [2100,3900,4000] if cols==3 else [2500]*cols)
    if cols>4:widths=[10000//cols]*cols
    parts=['<w:tbl><w:tblPr><w:tblStyle w:val="LabTable"/><w:tblW w:w="10000" w:type="dxa"/><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>']
    parts.extend(f'<w:gridCol w:w="{w}"/>' for w in widths);parts.append('</w:tblGrid>')
    for i,row in enumerate(rows):
        parts.append('<w:tr><w:trPr>'+('<w:tblHeader/>' if i==0 else '')+'<w:cantSplit/></w:trPr>')
        for col in range(cols):
            text=row[col] if col<len(row) else ''
            shade='<w:shd w:fill="E4EDF3"/>' if i==0 else ('<w:shd w:fill="F4F7F9"/>' if i%2==0 else '')
            parts.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[col]}" w:type="dxa"/>{shade}</w:tcPr>'+paragraph(text,'TableHead' if i==0 else 'TableText')+'</w:tc>')
        parts.append('</w:tr>')
    parts.append('</w:tbl>');parts.append(paragraph())
    return ''.join(parts)


def screenshot(caption, relative_path):
    """Embed a local PNG, preserving aspect ratio and keeping its caption attached."""
    path = (LAB / relative_path).resolve()
    if not path.is_relative_to(LAB.resolve()):
        raise ValueError('Screenshot must be inside the selected lab directory')
    private_path = PRIVATE / (path.stem + '-private.png')
    if args.private_evidence and private_path.is_file():
        path = private_path
        caption = caption.replace('live answer masked', 'live answer shown in this private copy')
        caption = caption.replace('the live database identity is masked in this distributable capture', 'the live database identity is visible in this private copy')
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Only PNG screenshots are supported: ' + relative_path)
    width, height = struct.unpack('>II', data[16:24])
    number = len(images) + 1
    rid = 'rIdImage' + str(number)
    target = 'media/screenshot' + str(number) + '.png'
    images.append((rid, target, data))
    cx = 6350000  # 10,000 twips: the document's content width.
    cy = round(cx * height / width)
    if cy > 6858000:
        cx = round(cx * 6858000 / cy)
        cy = 6858000
    drawing = f'''<w:p><w:pPr><w:keepNext/></w:pPr><w:r><w:drawing>
<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{number}" name="Screenshot {number}" descr={quoteattr(caption)}/>
<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{number}" name="Screenshot {number}"/><pic:cNvPicPr/></pic:nvPicPr>
<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>
</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
    return drawing + paragraph(caption, 'TableText')


def markdown(text,drop_title=False):
    lines=text.splitlines();parts=[];i=0
    while i<len(lines):
        line=lines[i];s=line.strip()
        if not s:i+=1;continue
        img = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', s)
        if img:
            parts.append(screenshot(img.group(1), img.group(2)));i+=1;continue
        if s.startswith('```'):
            i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):
                # Keep long SQL/source lines legible in portrait pages without losing text.
                parts.append(paragraph(lines[i].rstrip(),'Code'));i+=1
            parts.append(paragraph());i+=1;continue
        if s.startswith('|') and i+1<len(lines) and re.match(r'^\s*\|[\s:|\-]+\|\s*$',lines[i+1]):
            rows=[[c.strip() for c in s.strip('|').split('|')]];i+=2
            while i<len(lines) and lines[i].strip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]);i+=1
            parts.append(table(rows));continue
        h=re.match(r'^(#{1,4})\s+(.+)',s)
        if h:
            level=len(h.group(1));title=h.group(2)
            if not(drop_title and level==1):
                b=None;newpage=False
                m=re.match(r'Lab (\d+):',title)
                if m:b='lab_'+m.group(1);newpage=True
                parts.append(paragraph(title,'Heading'+str(min(level,3)),b,newpage))
            i+=1;continue
        if re.match(r'^[-*] ',s):
            parts.append(paragraph('• '+s[2:],'List'));i+=1;continue
        if re.match(r'^\d+\. ',s):
            parts.append(paragraph(s,'List'));i+=1;continue
        parts.append(paragraph(s));i+=1
    return ''.join(parts)


body=[paragraph('ORACLE PRIVATE AGENT FACTORY','Subtitle'),
      paragraph('Build a Database\nMonitoring Agent'.replace('\n',' '),'Title'),
      paragraph('PAF Configuration Only' if args.paf_only else 'Step-by-step LiveLab','Subtitle'),
      paragraph('Prepared database • PAF connections • Select AI profile • Agent Builder • Validation' if args.paf_only else 'Database setup • Select AI profile • Agent Builder • Validation'),
      paragraph('September 2026 | Workshop guide and complete appendices'),
      paragraph('Estimated duration: 60–75 minutes. Database preparation completed by the facilitator.' if args.paf_only else 'Estimated duration: 90–120 minutes. Existing-environment fast path: 45–60 minutes.'),
      paragraph('Local workshop package based on the tested monitoring MVP; not an officially published Oracle LiveLabs offering.'),
      paragraph('Workshop navigation','Heading2')]
for n,label in enumerate(NAVIGATION,1):
    body.append(f'<w:p><w:hyperlink w:anchor="lab_{n}">'+run(f'Lab {n}: {label}')+'</w:hyperlink></w:p>')
body.append(paragraph('Workshop guide','Heading1',page_break=True))
if args.private_evidence:
    body.append(paragraph('PRIVATE EVIDENCE COPY — contains live monitoring answers. Keep outside version control and review before sharing. Account identifiers and credentials remain masked. The public-guide references to masked answers describe the distributable version; this copy substitutes the private response screenshots where available.','Heading2'))
body.append(markdown((LAB/'README.md').read_text(),drop_title=True))
for letter,title,file in APPENDICES:
    body.append(paragraph(f'Appendix {letter}: {title}','Heading1','appendix_'+letter.lower(),True))
    body.append(paragraph('Source file: '+file,'TableText'))
    text=(LAB/'files'/file).read_text()
    if file.endswith('.sql'):
        body.append(paragraph('Reference source: '+file+'. Use the supplied .sql file when executing; preserve punctuation and line breaks.'))
        body.extend(paragraph(line,'Code') for line in text.splitlines())
    elif file.endswith('.txt'):
        body.append(paragraph('Copy the following complete text into the Agent Custom instructions field.'))
        body.extend(paragraph(line,'PromptText') for line in text.splitlines())
    else:body.append(markdown(text,drop_title=True))
body.append('''<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1000" w:right="953" w:bottom="1000" w:left="953" w:header="450" w:footer="450"/><w:titlePg/></w:sectPr>''')
document=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'+''.join(body)+'</w:body></w:document>'
styles=f'''<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="110" w:line="265" w:lineRule="auto"/><w:widowControl/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:pPr><w:spacing w:before="800" w:after="350"/></w:pPr><w:rPr><w:b/><w:color w:val="183B50"/><w:sz w:val="56"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:pPr><w:spacing w:before="200" w:after="200"/></w:pPr><w:rPr><w:color w:val="42697C"/><w:sz w:val="28"/></w:rPr></w:style>
'''
for level,size in [(1,36),(2,29),(3,24)]:
    styles+=f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="heading {level}"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="260" w:after="160"/><w:outlineLvl w:val="{level-1}"/></w:pPr><w:rPr><w:b/><w:color w:val="183B50"/><w:sz w:val="{size}"/></w:rPr></w:style>'
for name,props,rprops in [
    ('Code','<w:spacing w:before="0" w:after="0" w:line="220" w:lineRule="auto"/><w:shd w:fill="F0F3F5"/>','<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/>'),
    ('List','<w:ind w:left="280" w:hanging="240"/>',''),
    ('TableText','<w:spacing w:after="65" w:line="235" w:lineRule="auto"/>','<w:sz w:val="19"/>'),
    ('TableHead','<w:keepNext/><w:spacing w:after="65"/>','<w:b/><w:sz w:val="19"/>'),
    ('PromptText','<w:spacing w:after="85"/>','<w:sz w:val="20"/>')]:
    styles+=f'<w:style w:type="paragraph" w:styleId="{name}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/><w:pPr>{props}</w:pPr><w:rPr>{rprops}</w:rPr></w:style>'
styles+='''<w:style w:type="table" w:styleId="LabTable"><w:name w:val="Lab Table"/><w:tblPr><w:tblBorders>'''+''.join(f'<w:{x} w:val="single" w:sz="4" w:color="CBD5DC"/>' for x in ['top','left','bottom','right','insideH','insideV'])+'''</w:tblBorders><w:tblCellMar><w:top w:w="90" w:type="dxa"/><w:left w:w="110" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style></w:styles>'''
rel_ns='http://schemas.openxmlformats.org/package/2006/relationships'
rels=f'<Relationships xmlns="{rel_ns}">'
for rid,kind,target in [('rIdStyles','styles','styles.xml'),('rIdHeader','header','header1.xml'),('rIdFooter','footer','footer1.xml')]:rels+=f'<Relationship Id="{rid}" Type="{R}/{kind}" Target="{target}"/>'
for rid,target in relationships:rels+=f'<Relationship Id="{rid}" Type="{R}/hyperlink" Target={quoteattr(target)} TargetMode="External"/>'
for rid,target,_ in images:rels+=f'<Relationship Id="{rid}" Type="{R}/image" Target={quoteattr(target)}/>'
rels+='</Relationships>'
content_types='''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'''
for part,kind in [('document','document.main'),('styles','styles'),('header1','header'),('footer1','footer')]:content_types+=f'<Override PartName="/word/{part}.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.{kind}+xml"/>'
content_types+='</Types>'
if images:
    content_types = content_types.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>')
files={'[Content_Types].xml':content_types,'_rels/.rels':f'<Relationships xmlns="{rel_ns}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>',
'word/document.xml':document,'word/styles.xml':styles,'word/_rels/document.xml.rels':rels,
'word/header1.xml':f'<w:hdr xmlns:w="{W}">'+paragraph('DATABASE MONITORING AGENT | LIVELAB','TableText')+'</w:hdr>',
'word/footer1.xml':f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr>'+run('Oracle Private Agent Factory  •  ')+ '<w:fldSimple w:instr="PAGE"/></w:p></w:ftr>'}
for name,text in files.items():ET.fromstring(text)
OUT.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for name,text in files.items():z.writestr(name,text.encode('utf-8'))
    for _,target,data in images:z.writestr('word/'+target,data)
with zipfile.ZipFile(OUT) as z:
    assert z.testzip() is None
    doc=ET.fromstring(z.read('word/document.xml'))
    actual_anchors={e.attrib['{'+W+'}name'] for e in doc.iter('{'+W+'}bookmarkStart')}
    assert set(anchors.values())<=actual_anchors
    assert {f'lab_{n}' for n in range(1,8)}<=actual_anchors
    for e in doc.iter('{'+W+'}hyperlink'):
        a=e.attrib.get('{'+W+'}anchor')
        if a:assert a in actual_anchors
    text=''.join(doc.itertext())
    for _, _, f in APPENDICES:assert f in text
    for _,target,_ in images:assert 'word/'+target in z.namelist()
if args.private_evidence:
    OUT.chmod(0o600)
print(OUT)
print(f'Validated DOCX package: {OUT.stat().st_size:,} bytes; {len(actual_anchors)} navigation bookmarks; {len(images)} screenshots.')
