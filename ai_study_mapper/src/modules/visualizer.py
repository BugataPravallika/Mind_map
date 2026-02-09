import os
from typing import List

class Visualizer:
    """
    Generates academic radial spider maps for effective revision.
    """

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_static_diagram(self, structure: dict, quiz: List[dict], filename: str = "study_map.html") -> str:
        """
        Generates a true radial spider map with clean infographic aesthetics.
        """
        topic = structure.get("central_topic", "Study Map")
        branches = structure.get("branches", [])
        
        # Color mapping based on user rules
        colors = {
            "CENTER": "#1E3A8A",      # Dark Blue
            "CORE": "#2563EB",        # Blue
            "SUPPORTING": "#60A5FA",  # Light Blue
            "EXAMPLE": "#10B981",     # Green
            "HARD": "#EF4444",        # Red
            "MEDIUM": "#F59E0B",      # Orange
        }

        branch_html = ""
        for i, b in enumerate(branches):
            nodes_html = ""
            for n in b.get("nodes", []):
                cat = n.get("category", "SUPPORTING").upper()
                bg = colors.get(cat, colors["SUPPORTING"])
                icon = "🎯" if cat == "CORE" else ("💡" if cat == "SUPPORTING" else "📝")
                nodes_html += f'<div class="sub-node" style="background: {bg}">{icon} {n.get("text", "")}</div>'
            
            diff = b.get("difficulty", "Medium").upper()
            border_color = colors.get(diff, colors["MEDIUM"])
            
            # Position logic for radial layout (calculated in JS, but setup here)
            branch_html += f"""
            <div class="branch-group" id="branch-{i}" data-index="{i}">
                <div class="branch-node" style="border: 3px solid {border_color}">
                    <strong>{b.get('title', 'Concept')}</strong>
                </div>
                <div class="sub-nodes-container">
                    {nodes_html}
                </div>
            </div>
            """

        # MCQ Section with strict A, B, C, D format
        quiz_html = ""
        for i, q in enumerate(quiz or []):
            options_html = ""
            letters = ["A", "B", "C", "D"]
            for idx, opt in enumerate(q.get('options', [])[:4]):
                options_html += f'<div>{letters[idx]}. {opt}</div>'
            
            quiz_html += f"""
            <div class="mcq-card">
                <div style="font-weight: 700; margin-bottom: 10px;">Q{i+1}. {q['question']}</div>
                <div class="mcq-options">{options_html}</div>
                <div class="mcq-answer">✔ Correct Answer: {q['answer']}</div>
            </div>
            """

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{topic} Revision Sheet</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
        
        body {{
            font-family: 'Outfit', sans-serif;
            background-color: #FFFFFF;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
        }}

        .map-section {{
            width: 100vw;
            height: 800px;
            position: relative;
            background: radial-gradient(circle, #fcfcfc 0%, #ffffff 100%);
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        #map-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
        }}

        .center-topic {{
            background: {colors['CENTER']};
            color: white;
            padding: 25px 50px;
            border-radius: 20px;
            font-size: 28px;
            font-weight: 700;
            z-index: 10;
            box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3);
            text-align: center;
            max-width: 300px;
            cursor: default;
        }}

        .branch-group {{
            position: absolute;
            z-index: 5;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: transform 0.3s ease;
        }}

        .branch-node {{
            background: white;
            padding: 12px 25px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            text-align: center;
            white-space: nowrap;
        }}

        .sub-nodes-container {{
            margin-top: 15px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            align-items: center;
        }}

        .sub-node {{
            padding: 6px 15px;
            border-radius: 8px;
            font-size: 13px;
            color: white;
            font-weight: 500;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            max-width: 150px;
            text-align: center;
            white-space: normal;
        }}

        .quiz-section {{
            width: 900px;
            padding: 50px;
            background: #F8FAFC;
            border-top: 2px dashed #E2E8F0;
        }}

        .mcq-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        }}

        .mcq-options {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 15px 0;
            font-size: 14px;
            color: #475569;
        }}

        .mcq-answer {{
            font-size: 13px;
            color: #10B981;
            font-weight: 600;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #F1F5F9;
        }}

        @media print {{
            .map-section {{ height: auto; padding: 50px 0; }}
            .sub-node {{ color: black !important; border: 1px solid #ccc; }}
        }}
    </style>
</head>
<body>
    <div class="map-section" id="canvas">
        <svg id="map-svg"></svg>
        <div class="center-topic" id="center-node">{topic}</div>
        {branch_html}
    </div>

    <div class="quiz-section">
        <h2 style="margin-top: 0; color: #1E3A8A;">✍️ Final Knowledge Check</h2>
        <p style="color: #64748B; margin-bottom: 30px;">Strict Multiple Choice Assessment based on the Mind Map above.</p>
        {quiz_html}
    </div>

    <script>
        function layoutMap() {{
            const canvas = document.getElementById('canvas');
            const center = document.getElementById('center-node');
            const branches = document.querySelectorAll('.branch-group');
            const svg = document.getElementById('map-svg');
            
            const radius = 300;
            const centerX = canvas.offsetWidth / 2;
            const centerY = canvas.offsetHeight / 2;
            
            svg.innerHTML = '';

            branches.forEach((branch, i) => {{
                const angle = (i * (360 / branches.length)) * (Math.PI / 180);
                const x = centerX + radius * Math.cos(angle) - branch.offsetWidth / 2;
                const y = centerY + radius * Math.sin(angle) - branch.offsetHeight / 2;
                
                branch.style.left = x + 'px';
                branch.style.top = y + 'px';
                
                // Draw Curved Line
                const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const bX = x + branch.offsetWidth / 2;
                const bY = y + branch.offsetHeight / 2;
                
                const controlX = centerX + (bX - centerX) * 0.5;
                const d = `M ${{centerX}} ${{centerY}} C ${{controlX}} ${{centerY}}, ${{controlX}} ${{bY}}, ${{bX}} ${{bY}}`;
                
                path.setAttribute("d", d);
                path.setAttribute("stroke", "#CBD5E1");
                path.setAttribute("stroke-width", "2");
                path.setAttribute("fill", "none");
                svg.appendChild(path);
            }});
        }}

        window.onload = layoutMap;
        window.onresize = layoutMap;
        setTimeout(layoutMap, 500);
    </script>
</body>
</html>
        """
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path
