from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_MODEL = os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash-002')  # デフォルト値を設定
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
database_id = os.getenv('NOTION_DATABASE_ID')

# Validate environment variables
if not all([GOOGLE_API_KEY, NOTION_API_KEY, database_id]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# 列名、プロンプト、Notionデータ型の定義
column_configs = {
    "Name": {
        "prompt": """Extract the paper title and translate it to Japanese.
Output in the following format only, nothing else:

## Name
[Original English Title] ([Japanese Translation])

Example:
## Name
Attention Is All You Need (注意機構がすべて)

Rules:
1. Keep the original English title exactly as written in the paper
2. Japanese translation should be in parentheses
3. Do not include any other information
4. Do not include paper authors, dates, or other metadata
5. Must start with '## Name'""",
        "notion_type": "title",
        "database_property": True,
        "required": True,
        "process_first": True  # タイトルを最初に処理することを示すフラグ
    },
    "どんな研究？": {
        "prompt": "この研究は何を目的とし、どのような成果を上げたのか",
        "notion_type": "rich_text",
        "database_property": True,  # ページ本文としてのみ表示
        "required": True
    },
    "新規性は？": {
        "prompt": "既存研究と比較して、どのような新しい点があるのか",
        "notion_type": "rich_text",
        "database_property": False,
    },
    "手法のキモは？": {
        "prompt": "提案手法の核となる技術や考え方",
        "notion_type": "rich_text",
        "database_property": True,
        "required": True
    },
    "検証方法は？": {
        "prompt": "実験や評価方法、結果の概要",
        "notion_type": "rich_text",
        "database_property": False,
        "required": True
    },
    "課題は？": {
        "prompt": "研究の限界や今後の課題として挙げられている点",
        "notion_type": "rich_text",
        "database_property": False,
        "required": True
    },
    "次に読む論文等は？": {
        "prompt": "関連研究や次に読むべき論文を以下の形式で列挙して。タイトル（可能ならリンク）。レスポンスはリストやjsonではなくあくまでテキストでお願いします。",
        "notion_type": "rich_text",
        "database_property": True,
        "required": True
    },
    "Keywords": {
        "prompt": "List 3-5 important technical keywords from the paper in English. Use commas to separate keywords. Example: deep learning, computer vision, neural networks",
        "notion_type": "multi_select",
        "database_property": True,  # データベースの列として追加
        "required": True
    },
    "研究の目的と背景": {
        "prompt": "研究の目的と背景を2000文字以上でまとめるためのプロンプト: <purpose> 本研究の目的について、以下の観点を踏まえて詳細に説明してください: - 研究で解決しようとしている問題や達成しようとしている目標 - 研究の意義や重要性 - 研究の新規性や独自性 </purpose> <background> 本研究の背景について、以下の観点を踏まえて詳細に説明してください: - 研究分野の現状と課題 - 関連する先行研究とその限界や問題点 - 本研究の位置づけ </background> <note> - 論文の内容に忠実に、論文に書かれていない情報や著者の意図を超えた解釈は避けてください。 - 論文から直接引用する場合は、引用部分を明示してください。 - 読み手にわかりやすい文章構成を心がけ、段落構成を適切に行い、論理的な流れを意識してください。 - 専門用語には説明を加えてください。 - 簡潔かつ明瞭な表現を使用してください。 </note>",
        "notion_type": "rich_text",
        "database_property": False,  # ページ本文としてのみ表示
        "required": False
    },
    "論文内にある全ての図表の説明": {
        "prompt": """
        論文内にある全ての図表の説明を1500文字以上でまとめるためのプロンプト:
        <figures_and_tables> 論文内に含まれる図表の種類と数を以下の形式で明記してください:
        - 図（図解、グラフ、画像など）: [数]
        - 表: [数] </figures_and_tables>
        <content_and_purpose> 各図表の内容と目的について、以下の観点を踏まえて簡潔に説明してください:
        -図表が表現しているデータや情報の概要
        -図表が研究のどの部分に関連しているか（方法、結果、考察など）
        -図表の主要なメッセージや著者が伝えたい点 </content_and_purpose>
        <components_and_symbols> 図表の構成要素や記号の意味について、以下の観点を踏まえて説明してください:
        -軸ラベル、凡例、色分けなどの図表の構成要素
        -図表内で使用されている記号や略語の意味
        -グラフの種類（折れ線グラフ、棒グラフ、散布図など）とその意味 </components_and_symbols>
        <key_results> 図表から読み取れる主要な結果や傾向について、以下の観点を踏まえて要約してください:
        -図表に示されたデータや情報から明らかになる重要な結果
        -データの傾向、パターン、または異常値
        -図表の結果が研究の結論にどのように関連しているか </key_results>
        <additional_info> 図表だけでは伝えきれない重要な情報や、図表の解釈や含意について、著者の説明を要約してください。 </additional_info>
        <note> - 論文に掲載されている図表のみを扱い、図表の説明は論文の記述に基づいて行ってください。 - 読み手にわかりやすい文章構成を心がけ、図表の説明を論理的な順序で配置してください。 - 専門用語には説明を加え、簡潔かつ明瞭な文章で説明してください。 </note>
        """.strip(),
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
    "論文内で結果の解釈や考察": {
        "prompt": "論文内で結果の解釈や考察がどのようにまとめられているかを3000文字以上でまとめるためのプロンプト: <structure> 結果の解釈や考察の全体的な構成について、以下の観点を踏まえて説明してください: - 結果の解釈や考察が論文のどの部分で行われているか - 解釈や考察の流れや論理構成 - 著者が重要視している点や強調している内容 </structure> <interpretations> 個々の結果に対する解釈や考察について、以下の観点を踏まえて詳細に説明してください: - 各結果が持つ意味や示唆についての著者の解釈 - 結果が研究の目的や仮説とどのように関連しているか - 結果の解釈が先行研究や関連分野の知見とどのように関連しているか </interpretations> <arguments> 結果の解釈や考察における著者の主張や論点について、以下の観点を踏まえて明確に述べてください: - 著者が結果から導き出した主要な主張や結論 - 著者が提示する新しい知見や洞察 - 著者が結果の解釈を通じて示唆する今後の研究の方向性 </arguments> <validity> 結果の解釈や考察の妥当性や限界について、以下の観点を踏まえて議論してください: - 著者の解釈や主張を裏付けるエビデンスの強さ - 結果の解釈における仮定や前提条件 - 結果の解釈が持つ限界や対象となる範囲 </validity> <note> - 論文の内容に忠実に、論文に明示的に書かれている解釈や考察のみを扱ってください。 - 論文に書かれていない推測や主観的な評価は避けてください。 - 必ず論文から直接引用してください。引用部分を明示してください。 - 読み手にわかりやすい文章構成を心がけ、段落構成を適切に行い、論理的な流れを意識してください。 - 専門用語には説明を加えてください。 - 著者の主張や論点を明確に伝える文章表現を使用してください。 </note>",
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
    "提案手法の新規性と既存研究との差異": {
        "prompt": """
        提案手法の新規性と既存研究との差異を1500文字以上でまとめるためのプロンプト:
        <key_contributions> 提案手法の主要な特徴や貢献について、以下の観点を踏まえて明確にしてください:
        - 提案手法の中核をなすアイデアや技術
        - 提案手法の独自性や有効性を裏付ける要素
        - 提案手法の特徴や貢献が論文のどの部分で強調されているか（引用を含めて）
        </key_contributions>
        <related_work_comparison> 提案手法と関連研究の類似点と相違点について、以下の観点を踏まえて詳細に比較してください:
        - 提案手法と関連研究の手法やアプローチの共通点
        - 提案手法が関連研究と異なる点や改善点
        - 比較の結果が論文のどの部分で議論されているか（引用を含めて）
        </related_work_comparison>
        <novelty_superiority> 提案手法の新規性や優位性について、以下の観点を踏まえて具体的に説明してください:
        - 提案手法が解決する既存研究の問題点や限界
        - 提案手法がもたらす新しい洞察や可能性
        - 新規性や優位性が論文のどの部分で主張されているか（引用を含めて）
        </novelty_superiority>
        <effectiveness> 提案手法の有効性を実験結果や評価指標に基づいて以下の観点を踏まえて説明してください: - 提案手法の性能が関連研究を上回っている点 - 提案手法の有効性を裏付ける実験結果や評価指標 - 実験結果や評価指標が論文のどの部分で報告されているか（引用を含めて） </effectiveness>
        <limitations_future_work> 提案手法の限界や今後の改善点について、以下の観点を踏まえて言及してください:
        - 提案手法の制約や適用範囲の限界
        - 提案手法の改善や拡張の可能性についての著者の見解
        - 限界や改善点が論文のどの部分で討議されているか（引用を含めて）
        </limitations_future_work>
        <info_availability> 論文中に提案手法の新規性や既存研究との差異について詳細な情報が記載されていない場合は、以下の文章を記載してください: 「論文中に提案手法の新規性や既存研究との差異の詳細な情報が見当たりません。著者への問い合わせや補足資料の確認が必要かもしれません。」 </info_availability>
        <note> - 論文で実際に主張・議論されている新規性や差異の情報のみを扱い、説明は論文の記述に基づいて行ってください。 - 読み手にわかりやすい文章構成を心がけ、説明を論理的な順序で配置してください。 - 専門用語には説明を加え、簡潔かつ明瞭な文章で説明してください。- 必ず論文から直接引用してください。引用部分を明示してください。 </note>
        """.strip(),
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
    "論文内の数式と手法の関連": {
        "prompt": "論文内の数式と手法の関連を2500文字以上でまとめるためのプロンプト: <equations> 論文で提示されている全ての数式について、以下の観点を踏まえて詳細に説明してください: - 各数式の意味や役割 - 数式が手法のどの部分に対応しているか - 数式がどのように手法の実装や動作に寄与しているか - 数式のパラメータや変数が手法のどの要素を表しているか </equations> <derivation> 各数式の導出過程や理論的背景について、以下の観点を踏まえて詳細に説明してください: - 数式がどのような前提条件や仮定に基づいて導出されたか - 数式の理論的根拠や、関連する定理・原理 - 数式の一般性や適用範囲 </derivation> <impact> 数式と手法の関連性が結果にどのように影響しているかについて、以下の観点を踏まえて考察してください: - 数式のパラメータ設定が手法の性能にどのように影響するか - 数式の変更や拡張が手法の改善にどのようにつながるか </impact> <note> - 論文の内容に忠実に、論文に明示的に書かれている数式と手法の関連性のみを扱ってください。 - 論文に書かれていない解釈や推測は避けてください。- 必ず論文から直接引用してください。引用部分を明示してください。 - 読み手にわかりやすい文章構成を心がけ、段落構成を適切に行い、論理的な流れを意識してください。 - 専門用語には説明を加えてください。 - 図表や数式のレンダリングを活用して、理解を助けてください。- LaTeX形式で出力してください。また出力する際には$${数式}$$という形式で、数式を$${と}$$で囲むようにしてください </note>",
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
    "研究の限界や課題に関する要約": {
        "prompt": "論文内で研究の限界や課題がどのようにまとめられているかを2000文字以上でまとめるためのプロンプト: <limitations> 研究の限界について、著者がどのように説明しているかを以下の観点を踏まえて詳細に報告してください: - 研究の方法論、データ、解析手法などにおける限界 - 結果の解釈や一般化における限界 - 研究の対象や適用範囲が持つ限界 </limitations> <challenges> 研究の課題について、著者がどのように説明しているかを以下の観点を踏まえて詳細に報告してください: - 現在の研究で解決できなかった問題や疑問点 - 研究の結果や解釈を更に発展させるために必要な追加の研究課題 - 研究の方法論や理論的枠組みに関する課題や改善点 </challenges> <implications> 研究の限界や課題が持つ意味や影響について、著者の見解を以下の観点を踏まえて要約してください: - 限界や課題が研究の結論や貢献にどのように影響するか - 限界や課題を踏まえた上で、研究の意義や価値をどのように主張しているか </implications> <note> - 論文の内容に忠実に、論文に明示的に書かれている限界や課題のみを扱ってください。 - 論文に書かれていない推測や主観的な評価は避けてください。- 必ず論文から直接引用してください。引用部分を明示してください。 - 読み手にわかりやすい文章構成を心がけ、段落構成を適切に行い、論理的な流れを意識してください。 - 専門用語には説明を加えてください。 - 限界や課題の要点を明確に伝える文章表現を使用してください。 </note>",
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
    "論文内で将来の展望や示唆に関する要約": {
        "prompt": """
        論文内で将来の展望や示唆がどのようにまとめられているかを2000文字以上でまとめるためのプロンプト:<future_directions> 著者が提示する将来の研究の方向性や可能性について、以下の観点を踏まえて詳細に報告してください:
        -現在の研究を発展させるための具体的な研究課題や方法論
        -研究結果から導き出される新たな仮説や理論的示唆
        -他の研究分野への応用可能性や学際的な発展の可能性 </future_directions>
        <practical_implications> 著者が示唆する研究の応用や実践的示唆について、以下の観点を踏まえて詳細に報告してください:
        -研究結果を実社会の問題解決にどのように活用できるか
        -研究で得られた知見に基づく具体的な応用例や実践的な提言
        -研究の社会的意義や影響 </practical_implications>
        <author_views> 将来の展望や示唆における著者の主張や見解について、以下の観点を踏まえて明確に述べてください:
        -著者が特に重要視している発展の可能性や応用分野
        -著者が将来の研究や応用に向けて提供する独自の視点や洞察
        -著者が展望する研究の長期的な目標や期待される成果 </author_views>
        <note> - 論文の内容に忠実に、論文に明示的に書かれている将来の展望や示唆のみを扱ってください。 - 論文に書かれていない推測や主観的な評価は避けてください。- 必ず論文から直接引用してください。引用部分を明示してください。 - 読み手にわかりやすい文章構成を心がけ、段落構成を適切に行い、論理的な流れを意識してください。 - 専門用語には説明を加えてください。 - 将来の展望や示唆の要点を明確に伝える文章表現を使用してください。 </note>
        """.strip(),
        "notion_type": "rich_text",
        "database_property": False,
        "required": False
    },
}
