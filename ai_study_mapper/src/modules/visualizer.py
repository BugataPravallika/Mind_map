import os
from typing import List

class Visualizer:
    """
    Generates premium infographic-style study materials.
    """

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_static_diagram(self, structure: dict, quiz: List[dict], filename: str = "study_map.html") -> str:
        """
        Generates a premium, one-page revision mind map with SVG curved connections.
        """
        topic = structure.get("central_topic", "Study Map")
        branches = structure.get("branches", [])
        
        cat_colors = {
            "CORE": "#DBEAFE",      # Light Blue
            "SUPPORTING": "#EFF6FF", # Even lighter blue
            "EXAMPLE": "#DCFCE7",    # Green
        }
        
        def get_branch_style(difficulty):
            diff = difficulty.lower()
            if "hard" in diff: return "border: 2px solid #F87171; background: #FEF2F2;" # Red
            if "medium" in diff: return "border: 2px solid #60A5FA; background: #EFF6FF;" # Blue
            return "border: 2px solid #34D399; background: #ECFDF5;" # Green

        branch_html = ""
        for i, b in enumerate(branches):
            nodes_html = ""
            for n in b.get("nodes", []):
                cat = n.get("category", "SUPPORTING").upper()
                bg = cat_colors.get(cat, "#F3F4F6")
                icon = "🎯" if cat == "CORE" else ("💡" if cat == "SUPPORTING" else "📝")
                nodes_html += f'<div class="node {cat.lower()}" style="background: {bg}">{icon} {n.get("text", "")}</div>'
            
            style = get_branch_style(b.get("difficulty", "Medium"))
            # We add a unique wrapper for each branch to handle SVG connection anchoring
            branch_html += f"""
            <div class="branch-wrapper" id="branch-{i}">
                <div class="branch-header" style="{style}">
                    <strong>{b.get('title', 'Branch')}</strong>
                    <span class="diff-tag">{b.get('difficulty', 'Medium')}</span>
                </div>
                <div class="nodes-list">
                    {nodes_html}
                </div>
                <div class="mnemonic-tag">🧠 {b.get('mnemonic', '')}</div>
            </div>
            """

        quiz_html = "".join([f'<div class="quiz-card"><strong>Q{i+1}:</strong> {q["question"]}</div>' for i, q in enumerate(quiz or [])])

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{topic} - Revision Sheet</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #F1F5F9;
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
        }}

        .revision-sheet {{
            width: 1100px;
            background: white;
            padding: 50px;
            border-radius: 30px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.05);
            position: relative;
            z-index: 1;
        }}

        .header {{
            text-align: center;
            margin-bottom: 80px;
        }}

        .main-topic {{
            background: #2563EB;
            color: white;
            padding: 25px 50px;
            border-radius: 60px;
            display: inline-block;
            font-size: 32px;
            font-weight: 700;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.4);
            position: relative;
            z-index: 10;
        }}

        .mind-map-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px 150px;
            position: relative;
        }}

        .branch-wrapper {{
            background: #F8FAFC;
            padding: 25px;
            border-radius: 20px;
            border: 1px solid #E2E8F0;
            position: relative;
            z-index: 5;
        }}

        .branch-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            border-radius: 12px;
            font-size: 20px;
            margin-bottom: 20px;
        }}

        .diff-tag {{
            font-size: 10px;
            text-transform: uppercase;
            font-weight: 800;
            padding: 3px 10px;
            border-radius: 6px;
            background: rgba(255,255,255,0.8);
        }}

        .nodes-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .node {{
            padding: 10px 16px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            border: 1px solid rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .node.core {{ border-left: 5px solid #2563EB; font-weight: 600; }}
        .node.supporting {{ border-left: 5px solid #60A5FA; }}
        .node.example {{ border-left: 5px solid #10B981; font-style: italic; background: #F0FDF4 !important; }}

        .mnemonic-tag {{
            margin-top: 20px;
            font-size: 12px;
            color: #475569;
            background: white;
            padding: 10px;
            border-radius: 10px;
            border: 1px dashed #CBD5E1;
            line-height: 1.4;
        }}

        #map-connections {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 2;
        }}

        .quiz-panel {{
            margin-top: 80px;
            padding: 40px;
            background: #F0F9FF;
            border-radius: 24px;
            border-left: 8px solid #0EA5E9;
        }}

        .quiz-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-top: 30px;
        }}

        .quiz-card {{
            background: white;
            padding: 20px;
            border-radius: 14px;
            font-size: 15px;
            border: 1px solid #E0F2FE;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }}

        .footer {{
            text-align: center;
            margin-top: 60px;
            font-size: 13px;
            color: #64748B;
            letter-spacing: 0.5px;
        }}

        @media print {{
            body {{ background: white; padding: 0; }}
            .revision-sheet {{ box-shadow: none; border: none; width: 100%; }}
            #map-connections {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="revision-sheet" id="sheet">
        <svg id="map-connections"></svg>
        
        <div class="header">
            <div class="main-topic" id="central-node">{topic}</div>
            <p style="margin-top: 25px; color: #64748B; font-weight: 500;">One-Page Revision Toolkit</p>
        </div>

        <div class="mind-map-grid">
            {branch_html}
        </div>

        <div class="quiz-panel">
            <h3 style="margin: 0; color: #0369A1; font-size: 24px;">✍️ Student Self-Check</h3>
            <div class="quiz-grid">
                {quiz_html}
            </div>
        </div>

        <div class="footer">
            Designed for clarity and stress reduction. You've got this! 🌟
        </div>
    </div>

    <script>
        function drawConnections() {{
            const svg = document.getElementById('map-connections');
            const central = document.getElementById('central-node');
            const sheet = document.getElementById('sheet');
            const branches = document.querySelectorAll('.branch-wrapper');
            
            const sheetRect = sheet.getBoundingClientRect();
            const centralRect = central.getBoundingClientRect();
            
            const centerX = centralRect.left + centralRect.width / 2 - sheetRect.left;
            const centerY = centralRect.top + centralRect.height / 2 - sheetRect.top;
            
            svg.innerHTML = ''; // Clear previous
            
            branches.forEach(branch => {{
                const bRect = branch.getBoundingClientRect();
                const bX = bRect.left + (bRect.left < centralRect.left ? bRect.width : 0) - sheetRect.left;
                const bY = bRect.top + bRect.height / 2 - sheetRect.top;
                
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                // Create a smooth curve (Cubic Bezier)
                const controlX = centerX + (bX - centerX) / 2;
                const d = `M ${{centerX}} ${{centerY}} C ${{controlX}} ${{centerY}}, ${{controlX}} ${{bY}}, ${{bX}} ${{bY}}`;
                
                path.setAttribute("d", d);
                path.setAttribute("stroke", "#E2E8F0");
                path.setAttribute("stroke-width", "3");
                path.setAttribute("fill", "none");
                svg.appendChild(path);
            }});
        }}
        
        // Initial draw and redraw on resize
        window.onload = drawConnections;
        window.onresize = drawConnections;
        setTimeout(drawConnections, 500); // Dynamic adjustment
    </script>
</body>
</html>
        """
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path
