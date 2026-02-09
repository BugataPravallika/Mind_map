import os
from typing import List

class Visualizer:
    """
    Visualizes the NetworkX graph using PyVis.
    """

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_static_diagram(self, structure: dict, quiz: List[dict], filename: str = "study_map.html") -> str:
        """
        Generates a unified "Printable Revision Sheet" with Map + Quiz.
        """
        topic = structure.get("central_topic", "Study Map")
        branches = structure.get("branches", [])
        
        # 1. Map Content
        colors = ["#FCD5CE", "#FAE1DD", "#F8EDEB", "#E8E8E4", "#D8E2DC", "#ECE4DB", "#FFE5D9", "#FFD7BA"]
        branch_html = ""
        for i, b in enumerate(branches):
            diff = b.get('difficulty', 'Medium').lower()
            diff_color = "#4CAF50" if "easy" in diff else ("#FF9800" if "hard" in diff else "#2196F3")
            
            mnemonic = b.get('mnemonic', '')
            mnemonic_html = f'<div class="mnemonic">💡 <strong>Hook:</strong> {mnemonic}</div>' if mnemonic else ""
            
            points_html = "".join([f"<li>{p}</li>" for p in b.get("points", [])])
            branch_html += f"""
            <div class="card">
                <div class="card-header">
                    <h3>{b.get('title', 'Branch')}</h3>
                    <span class="badge" style="background-color: {diff_color}">{b.get('difficulty', 'Medium')}</span>
                </div>
                <ul>{points_html}</ul>
                {mnemonic_html}
            </div>
            """

        # 2. Quiz Content
        quiz_html = ""
        answers_html = ""
        if quiz:
            for i, q in enumerate(quiz):
                options = "".join([f"<li>[ ] {opt}</li>" for opt in q.get('options', [])])
                quiz_html += f"""
                <div class="quiz-item">
                    <p><strong>Q{i+1}. {q['question']}</strong></p>
                    <ul style="list-style-type: none; padding-left: 10px;">{options}</ul>
                </div>
                """
                answers_html += f"""
                <p><strong>Q{i+1}. Correct Answer: {q['answer']}</strong><br>
                <i style="color: #666;">{q.get('explanation', '')}</i></p>
                """

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Verdana', sans-serif;
            background-color: #F8F9FA;
            color: #333;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
        }}
        .sheet {{
            max-width: 900px;
            margin: auto;
            background: white;
            padding: 50px;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
            border-radius: 4px;
        }}
        header {{
            text-align: center;
            border-bottom: 2px solid #EEE;
            margin-bottom: 40px;
            padding-bottom: 20px;
        }}
        .center-box {{
            background-color: #FFB7B2;
            padding: 15px 30px;
            border-radius: 8px;
            display: inline-block;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 30px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 50px;
        }}
        .card {{
            padding: 25px;
            border-radius: 12px;
            background: #FFF;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }}
        .card:hover {{ transform: translateY(-5px); }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            border-bottom: 1px solid #F1F5F9;
            padding-bottom: 10px;
        }}
        .badge {{
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .mnemonic {{
            margin-top: 15px;
            padding: 10px;
            background: #F8FAFC;
            border-radius: 8px;
            border-left: 4px solid #64748B;
            font-size: 0.9em;
            color: #475569;
        }}
        .card h3 {{
            margin: 0;
            font-size: 18px;
            color: #1E293B;
        }}
        .card ul {{ padding-left: 20px; margin: 0; color: #334155; }}
        
        .section-break {{
            border-top: 2px dashed #CBD5E1;
            margin: 50px 0;
            padding-top: 30px;
        }}
        .quiz-section h2 {{ color: #2563EB; font-size: 24px; }}
        .quiz-item {{ margin-bottom: 20px; padding: 20px; border-radius: 8px; background: #F0F9FF; border-left: 5px solid #0EA5E9; }}
        
        .answers-section {{
            background: #F8FAFC;
            padding: 25px;
            border-radius: 12px;
            margin-top: 40px;
            font-size: 0.9em;
            border: 1px solid #E2E8F0;
        }}
        
        @media print {{
            body {{ padding: 0; background: white; }}
            .sheet {{ box-shadow: none; width: 100%; max-width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="sheet">
        <header>
            <div class="center-box">{topic}</div>
            <p>Study Revision Diagram</p>
        </header>

        <div class="grid">
            {branch_html}
        </div>

        <div class="section-break"></div>

        <div class="quiz-section">
            <h2>✍️ Quick Self-Check</h2>
            <p>Take a few deep breaths and try these simple questions to build your confidence.</p>
            {quiz_html}
        </div>

        <div class="answers-section">
            <h3 style="margin-top:0;">Answers & Extra Help</h3>
            {answers_html}
        </div>
        
        <footer style="margin-top:50px; text-align:center; color:#999; font-size:12px;">
            Be kind to yourself. You are making great progress!
        </footer>
    </div>
</body>
</html>
        """
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

if __name__ == "__main__":
    # Test stub
    viz = Visualizer()
    struct = {"central_topic": "Test", "branches": [{"title": "B1", "points": ["P1"]}]}
    viz.generate_static_diagram(struct, [], "test_map.html")
