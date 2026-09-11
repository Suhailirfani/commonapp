import io
import re
import urllib.parse
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def reportlab_pdf_response(pdf_bytes, filename="document.pdf", request=None):
    clean_filename = re.sub(r'[\r\n\t"\\\/]', '_', str(filename)).strip()
    if not clean_filename.lower().endswith('.pdf'):
        clean_filename += '.pdf'
    encoded_filename = urllib.parse.quote(clean_filename)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    disposition_type = 'inline' if (request and (request.GET.get('preview') == '1' or request.GET.get('inline') == '1')) else 'attachment'
    response['Content-Disposition'] = f'{disposition_type}; filename="{clean_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    response['Content-Length'] = str(len(pdf_bytes))
    return response


def build_green_room_pdf(programs_data, institution_name, is_bulk=True):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14.5,
        leading=16.5,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=2
    )

    prog_title_style = ParagraphStyle(
        'ProgTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=14.5,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4
    )

    info_style = ParagraphStyle(
        'InfoText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=11.5,
        textColor=colors.black
    )

    th_center = ParagraphStyle(
        'THCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12.5,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    th_left = ParagraphStyle(
        'THLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    td_center_bold = ParagraphStyle(
        'TDCenterBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.black
    )

    td_name_bold = ParagraphStyle(
        'TDNameBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=12.5,
        alignment=TA_LEFT,
        textColor=colors.black
    )

    timing_style = ParagraphStyle(
        'Timing',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=11.5,
        spaceBefore=4,
        spaceAfter=3
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569'),
        spaceBefore=2
    )

    story = []
    total_progs = len(programs_data)

    for idx, pdata in enumerate(programs_data):
        prog = pdata['program']
        participants = pdata['participants']
        cat_name = prog.category.name if (hasattr(prog, 'category') and prog.category) else 'General'

        # 1. Header
        story.append(Paragraph("GREEN ROOM SIGN SHEET", title_style))
        story.append(Paragraph(str(prog.name).upper(), prog_title_style))
        sub_text = f"Category: {cat_name} &nbsp;|&nbsp; Institution: {institution_name}"
        story.append(Paragraph(sub_text, subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.black, spaceAfter=4, spaceBefore=0))

        # 2. Info Bar Table (width = 555pt)
        info_html = f"Program: <b>{str(prog.name).upper()}</b> &nbsp;|&nbsp; Category: <b>{cat_name}</b> &nbsp;|&nbsp; Total Participants: <b>{len(participants)}</b>"
        info_table = Table(
            [[Paragraph(info_html, info_style)]],
            colWidths=[555]
        )
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 4))

        # 3. Table
        if participants:
            table_data = [
                [
                    Paragraph("S.No", th_center),
                    Paragraph("Chest No", th_center),
                    Paragraph("Participant Name", th_left),
                    Paragraph("Code Letter", th_center),
                    Paragraph("Signature", th_center),
                ]
            ]

            for c_idx, part in enumerate(participants, 1):
                if prog.is_group:
                    c_no = f"#{part.captain.chest_no}" if (hasattr(part, 'captain') and part.captain) else "-"
                    p_name = part.team.name if hasattr(part, 'team') and part.team else ""
                    if hasattr(part, 'captain') and part.captain:
                        p_name += f" (Capt: {part.captain.name.upper()})"
                else:
                    c_no = str(part.chest_no) if hasattr(part, 'chest_no') else ""
                    p_name = part.name.upper() if hasattr(part, 'name') else ""

                table_data.append([
                    Paragraph(str(c_idx), td_center_bold),
                    Paragraph(c_no, td_center_bold),
                    Paragraph(p_name, td_name_bold),
                    "",
                    ""
                ])

            col_widths = [38, 72, 235, 80, 130]
            row_heights = [18] + [22] * len(participants)

            p_table = Table(table_data, colWidths=col_widths, rowHeights=row_heights)
            p_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(p_table)

            # 4. Timing
            timing_text = "Time Started: __________ AM/PM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Time Completed: __________ AM/PM"
            story.append(Paragraph(timing_text, timing_style))
        else:
            no_part_table = Table([[Paragraph("<b>No participants registered for this program yet.</b>", info_style)]], colWidths=[555])
            no_part_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(no_part_table)

        # 5. Footer
        foot_text = f"Green Room Sign Sheet &nbsp;|&nbsp; {prog.name}"
        story.append(Paragraph(foot_text, footer_style))

        # Bulk pagination: Exactly 2 programs per page
        if is_bulk and (idx < total_progs - 1):
            if (idx + 1) % 2 == 0:
                story.append(PageBreak())
            else:
                story.append(Spacer(1, 14))
                story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#64748b'), spaceAfter=14, spaceBefore=0, dash=[5, 4]))

    doc.build(story)
    return buffer.getvalue()
