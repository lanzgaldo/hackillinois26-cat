import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';
import { LegacyCompletedInspection, InspectionItem } from '../types/inspection';
import { CATEGORIES } from '../constants/inspectionCategories';

const getStatusColor = (status: string) => {
    switch (status) {
        case 'red': return '#CC2200';
        case 'yellow': return '#CC9900';
        case 'green': return '#2D7A2D';
        default: return '#888888';
    }
};

const getStatusLabel = (status: string) => {
    switch (status) {
        case 'red': return 'RED';
        case 'yellow': return 'YELLOW';
        case 'green': return 'GREEN';
        default: return 'SKIPPED';
    }
};

const getDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`;
};

const generateBaseHTML = (inspection: LegacyCompletedInspection, contentHTML: string) => `
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no" />
    <style>
        @page { margin: 40px; }
        body { 
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
            margin: 0; 
            padding: 0;
            color: #111111;
            background: #FFFFFF;
        }
        .header-bar {
            background-color: #FFCD11;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header-title { font-size: 22px; font-weight: bold; margin: 0; }
        .header-subtitle { font-size: 13px; font-weight: normal; margin-left: 10px; }
        .header-logo { font-size: 18px; font-weight: bold; margin: 0; }
        .meta-box {
            background-color: #F5F5F5;
            padding: 15px 20px;
            border-bottom: 2px solid #FFCD11;
            margin-bottom: 20px;
            font-size: 12px;
            color: #555555;
            line-height: 1.6;
        }
        .meta-box strong { color: #111111; }
        .footer {
            position: fixed;
            bottom: 0px;
            left: 0;
            width: 100%;
            border-top: 1px solid #DDDDDD;
            padding-top: 10px;
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #888888;
        }
        .content {
            padding-bottom: 50px; /* space for footer */
        }
        .category-header {
            background-color: #F0F0F0;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .item-row {
            padding: 12px 10px;
            border-bottom: 1px solid #EEEEEE;
        }
        .item-title { font-size: 14px; font-weight: bold; margin: 0 0 4px 0; }
        .item-category { font-size: 12px; color: #555555; margin: 0 0 8px 0; }
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            color: #FFFFFF;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .note {
            font-size: 12px;
            font-style: italic;
            margin-left: 15px;
            color: #555555;
            margin-bottom: 8px;
        }
        .photos {
            display: flex;
            gap: 10px;
            margin-top: 8px;
            margin-left: 15px;
        }
        .photo-thumb {
            width: 120px;
            height: 90px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #DDDDDD;
        }
        .timeline {
            font-size: 12px;
            color: #CC9900;
            margin-top: 6px;
            font-weight: bold;
        }
        .page-counter::after {
            content: counter(page);
        }
        .score-box {
            text-align: center;
            margin: 40px 0;
        }
        .score-num {
            font-size: 48px;
            font-weight: bold;
            margin: 0;
        }
        .score-label {
            font-size: 14px;
            color: #555555;
            text-transform: uppercase;
            margin-top: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        th, td {
            border: 1px solid #DDDDDD;
            padding: 10px;
            text-align: left;
            font-size: 12px;
        }
        th { background-color: #F9F9F9; font-weight: bold; }
        .action-callout {
            background-color: #FFF3CD;
            border: 1px solid #FFEEBA;
            color: #856404;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        .group-label {
            font-size: 14px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .sign-off {
            margin-top: 60px;
            border-top: 1px solid #111111;
            width: 300px;
            padding-top: 10px;
        }
        .sign-off-label {
            font-size: 12px;
            color: #555555;
        }
    </style>
</head>
<body>
    <div class="header-bar">
        <div>
            <span class="header-title">CAT TRACK</span>
            <span class="header-subtitle">INSPECTION REPORT</span>
        </div>
        <div class="header-logo">CAT&reg;</div>
    </div>
    
    <div class="meta-box">
        <div><strong>Inspector:</strong> ${inspection.inspectorName} &nbsp;|&nbsp; <strong>ID:</strong> #${inspection.inspectionId.slice(-6).toUpperCase()} &nbsp;|&nbsp; <strong>Submitted:</strong> ${new Date(inspection.submittedAt).toLocaleString()}</div>
        <div style="margin-top: 4px;"><strong>Asset ID:</strong> ${inspection.assetId} &nbsp;|&nbsp; <strong>S/N:</strong> ${inspection.serialNumber} &nbsp;|&nbsp; <strong>Model:</strong> ${inspection.model} ${inspection.customerName ? `&nbsp;|&nbsp; <strong>Customer:</strong> ${inspection.customerName}` : ''}</div>
        <div style="margin-top: 4px;"><strong>Duration:</strong> ${getDuration(inspection.elapsedSeconds)}</div>
    </div>

    <div class="content">
        ${contentHTML}
    </div>

    <div class="footer">
        <div>Generated by CAT Track &middot; caterpillar.com</div>
        <div>Page <span class="page-counter"></span></div>
        <div style="font-family: monospace;">${inspection.inspectionId}</div>
    </div>
</body>
</html>
`;

const renderItemHTML = (item: InspectionItem) => {
    const note = item.voiceNoteEditedTranscript || item.voiceNoteTranscript;
    const photoHTML = item.photos && item.photos.length > 0
        ? `<div class="photos">${item.photos.map(p => `<img src="${p}" class="photo-thumb" alt="inspection photo" onerror="this.outerHTML='<span style=\\'font-size:10px;color:#888;\\'>[Photo attached]</span>'"/>`).join('')}</div>`
        : '';

    return `
        <div class="item-row">
            <h4 class="item-title">${item.name}</h4>
            <p class="item-category">${item.category}</p>
            <div class="status-badge" style="background-color: ${getStatusColor(item.status)}">${getStatusLabel(item.status)}</div>
            ${item.status === 'yellow' && item.timelineEstimate ? `<div class="timeline">Address within: ${item.timelineEstimate}</div>` : ''}
            ${note ? `<div class="note">"${note}"</div>` : ''}
            ${photoHTML}
        </div>
    `;
};

const executePrint = async (html: string) => {
    try {
        const { uri } = await Print.printToFileAsync({ html });
        await Sharing.shareAsync(uri, {
            mimeType: 'application/pdf',
            dialogTitle: 'Share Inspection Report'
        });
    } catch (e) {
        throw new Error('PDF Generation Failed');
    }
}

export const generateFormOrderPDF = async (inspection: LegacyCompletedInspection) => {
    let content = '';
    CATEGORIES.forEach(category => {
        const itemsInCategory = inspection.items.filter(i => CATEGORIES.find(c => c.id === category.id)?.items.map(ci => ci.id).includes(i.id));
        if (itemsInCategory.length > 0) {
            content += `<div class="category-header" style="border-left: 4px solid #FFCD11;">${category.name}</div>`;
            itemsInCategory.forEach(item => {
                content += renderItemHTML(item);
            });
        }
    });

    const html = generateBaseHTML(inspection, content);
    await executePrint(html);
};

export const generateSeverityOrderPDF = async (inspection: LegacyCompletedInspection) => {
    let content = '';

    const redItems = inspection.items.filter(i => i.status === 'red').sort((a, b) => a.name.localeCompare(b.name));
    const yellowItems = inspection.items.filter(i => i.status === 'yellow').sort((a, b) => a.name.localeCompare(b.name));
    const greenItems = inspection.items.filter(i => i.status === 'green').sort((a, b) => a.name.localeCompare(b.name));
    const skipItems = inspection.items.filter(i => i.status !== 'red' && i.status !== 'yellow' && i.status !== 'green').sort((a, b) => a.name.localeCompare(b.name));

    if (redItems.length > 0) {
        content += `<div class="category-header" style="border-left: 4px solid #CC2200;">CRITICAL / RED</div>`;
        redItems.forEach(i => content += renderItemHTML(i));
    }
    if (yellowItems.length > 0) {
        content += `<div class="category-header" style="border-left: 4px solid #CC9900;">WARNING / YELLOW</div>`;
        yellowItems.forEach(i => content += renderItemHTML(i));
    }
    if (greenItems.length > 0) {
        content += `<div class="category-header" style="border-left: 4px solid #2D7A2D;">PASS / GREEN</div>`;
        greenItems.forEach(i => content += renderItemHTML(i));
    }
    if (skipItems.length > 0) {
        content += `<div class="category-header" style="border-left: 4px solid #888888;">SKIPPED / UNCHECKED</div>`;
        skipItems.forEach(i => content += renderItemHTML(i));
    }

    const html = generateBaseHTML(inspection, content);
    await executePrint(html);
};

export const generateSummaryReportPDF = async (inspection: LegacyCompletedInspection) => {
    let redCount = 0; let yellowCount = 0; let greenCount = 0; let skipCount = 0;
    inspection.items.forEach(i => {
        if (i.status === 'red') redCount++;
        else if (i.status === 'yellow') yellowCount++;
        else if (i.status === 'green') greenCount++;
        else skipCount++;
    });

    const total = redCount + yellowCount + greenCount + skipCount;
    const scoredTotal = redCount + yellowCount + greenCount;
    let score = 0; let scoreColor = '#2D7A2D';
    if (scoredTotal > 0) {
        score = Math.round(((greenCount * 1.0 + yellowCount * 0.5) / scoredTotal) * 100);
        if (score < 50) scoreColor = '#CC2200';
        else if (score < 80) scoreColor = '#CC9900';
    }

    let content = `
        <div class="score-box">
            <p class="score-num" style="color: ${scoreColor};">${score}</p>
            <p class="score-label">EQUIPMENT HEALTH SCORE</p>
        </div>

        <table>
            <tr>
                <th>Status</th>
                <th>Count</th>
                <th>% of Total</th>
                <th>Severity</th>
            </tr>
            <tr>
                <td style="color: #2D7A2D; font-weight: bold;">PASS (GREEN)</td>
                <td>${greenCount}</td>
                <td>${total > 0 ? Math.round((greenCount / total) * 100) : 0}%</td>
                <td>Normal</td>
            </tr>
            <tr>
                <td style="color: #CC9900; font-weight: bold;">WARNING (YELLOW)</td>
                <td>${yellowCount}</td>
                <td>${total > 0 ? Math.round((yellowCount / total) * 100) : 0}%</td>
                <td>Monitor</td>
            </tr>
            <tr>
                <td style="color: #CC2200; font-weight: bold;">CRITICAL (RED)</td>
                <td>${redCount}</td>
                <td>${total > 0 ? Math.round((redCount / total) * 100) : 0}%</td>
                <td>Immediate</td>
            </tr>
            <tr>
                <td style="color: #888888;">SKIPPED</td>
                <td>${skipCount}</td>
                <td>${total > 0 ? Math.round((skipCount / total) * 100) : 0}%</td>
                <td>N/A</td>
            </tr>
            <tr style="background-color: #F9F9F9; font-weight: bold;">
                <td>TOTAL</td>
                <td>${total}</td>
                <td>100%</td>
                <td>-</td>
            </tr>
        </table>

        <div style="margin-bottom: 30px;">
            <p style="font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 10px;">General Comments</p>
            <p style="font-size: 13px; color: #555555; line-height: 1.5;">${inspection.generalComments || 'No general comments recorded.'}</p>
        </div>
    `;

    if (inspection.aiReview) {
        content += `
            <div style="margin-bottom: 30px;">
                <p style="font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 10px;">AI-GENERATED OVERVIEW &mdash; ADVISORY ONLY</p>
                <div style="background-color: #F9F9F9; padding: 15px; border-left: 4px solid #FFCD11;">
                    <p style="font-size: 13px; color: #111; line-height: 1.6; margin-top: 0;">${inspection.aiReview.narrative}</p>
                    ${inspection.aiReview.urgentFlags.map(f => `<p style="color: #CC2200; font-size: 13px; margin: 5px 0;">&bull; ${f}</p>`).join('')}
                    <p style="font-size: 13px; color: #CC9900; font-weight: bold; margin-bottom: 0; margin-top: 15px;">Recommendation: ${inspection.aiReview.recommendedAction}</p>
                </div>
            </div>
        `;
    }

    content += `
        <div class="sign-off">
            <div class="sign-off-label">Inspector Signature</div>
            <div style="font-size: 14px; margin-top: 8px;"><strong>${inspection.inspectorName}</strong><span style="float:right; font-size: 12px; color: #555;">Date: ${new Date(inspection.submittedAt).toLocaleDateString()}</span></div>
        </div>
    `;

    const html = generateBaseHTML(inspection, content);
    await executePrint(html);
};

export const generateActionableItemsPDF = async (inspection: LegacyCompletedInspection) => {
    let content = '';
    const redItems = inspection.items.filter(i => i.status === 'red').sort((a, b) => a.name.localeCompare(b.name));
    const yellowItems = inspection.items.filter(i => i.status === 'yellow').sort((a, b) => a.name.localeCompare(b.name));

    if (redItems.length === 0 && yellowItems.length === 0) {
        throw new Error('No actionable items');
    }

    content += `
        <div class="action-callout">
            ACTION REQUIRED &mdash; ${redItems.length + yellowItems.length} items require attention
        </div>
    `;

    if (redItems.length > 0) {
        content += `<div class="group-label" style="color: #CC2200;">CRITICAL &mdash; IMMEDIATE ACTION</div>`;
        redItems.forEach(i => content += renderItemHTML(i));
    }

    if (yellowItems.length > 0) {
        content += `<div class="group-label" style="color: #CC9900;">MONITOR &mdash; ADDRESS WITHIN TIMELINE</div>`;
        yellowItems.forEach(i => content += renderItemHTML(i));
    }

    content += `
        <p style="font-size: 12px; font-style: italic; color: #555555; margin-top: 40px; text-align: center;">
            Parts order recommended for all RED items. Contact your Cat dealer for scheduling.
        </p>
    `;

    const html = generateBaseHTML(inspection, content);
    await executePrint(html);
};

