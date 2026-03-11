"""题库：50道题，5个维度各10题"""
from __future__ import annotations

from .models import Question, Dimension, QuestionType, MatchMode

QUESTION_BANK: list[Question] = [
    # ═══════════════════════════════════════
    # 逻辑推理 (logic) - 10 题
    # ═══════════════════════════════════════
    Question(
        id="logic-001", dimension=Dimension.LOGIC, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="数列：2, 6, 12, 20, 30, ?  下一个数字是什么？只回答数字。",
        answer="42", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="logic-002", dimension=Dimension.LOGIC, difficulty=1,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="所有的猫都是动物，所有的动物都需要水。那么以下哪个结论是正确的？\nA. 所有需要水的都是猫\nB. 所有的猫都需要水\nC. 有些猫不需要水\nD. 所有的动物都是猫",
        choices=["A", "B", "C", "D"],
        answer="B", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="logic-003", dimension=Dimension.LOGIC, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="一个房间里有3盏灯和3个开关，开关在房间外。你只能进房间一次。如何确定每个开关对应哪盏灯？请用一句话概述核心策略。",
        answer="开一个等一会关掉再开另一个",
        match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="logic-004", dimension=Dimension.LOGIC, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="帽子问题：A、B、C三人排成一列（C在最后能看到A和B，B能看到A，A谁也看不到）。有2顶白帽子和3顶黑帽子，每人戴一顶。C说不知道自己的颜色，B也说不知道。A能推断出自己戴的是什么颜色？只回答颜色。",
        answer="黑", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="logic-005", dimension=Dimension.LOGIC, difficulty=1,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="如果下雨，地面会湿。地面是湿的。以下哪个推理是正确的？\nA. 一定下过雨\nB. 不一定下过雨\nC. 一定没下过雨\nD. 信息不足，无法判断",
        choices=["A", "B", "C", "D"],
        answer="B", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="logic-006", dimension=Dimension.LOGIC, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="数列：1, 1, 2, 3, 5, 8, 13, ?  下一个数字是什么？只回答数字。",
        answer="21", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="logic-007", dimension=Dimension.LOGIC, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="有5个人（A-E）参加比赛排名。已知：A在B前面，C在D后面，E不是第一也不是最后，B在D前面，C不是第一。谁是第一名？只回答字母。",
        answer="A", match_mode=MatchMode.CONTAINS, points=20,
    ),
    Question(
        id="logic-008", dimension=Dimension.LOGIC, difficulty=2,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="农夫需要把狐狸、鸡和谷物运过河，船每次只能带一样东西。狐狸会吃鸡，鸡会吃谷物。农夫第一趟应该带什么过河？\nA. 狐狸\nB. 鸡\nC. 谷物\nD. 随便哪个都行",
        choices=["A", "B", "C", "D"],
        answer="B", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="logic-009", dimension=Dimension.LOGIC, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="甲说：'乙在说谎。' 乙说：'丙在说谎。' 丙说：'甲和乙都在说谎。' 这三人中有几个人在说谎？只回答数字。",
        answer="2", match_mode=MatchMode.EXACT, points=20,
    ),
    Question(
        id="logic-010", dimension=Dimension.LOGIC, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="一个钟表的时针和分针在12点重合后，下一次完全重合大约在几点几分？回答格式如 1:05。",
        answer="1:05", match_mode=MatchMode.CONTAINS, points=20,
    ),

    # ═══════════════════════════════════════
    # 知识广度 (knowledge) - 10 题
    # ═══════════════════════════════════════
    Question(
        id="know-001", dimension=Dimension.KNOWLEDGE, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="光在真空中的传播速度大约是每秒多少万公里？只回答数字。",
        answer="30", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-002", dimension=Dimension.KNOWLEDGE, difficulty=1,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="DNA的双螺旋结构是由谁发现的？\nA. 达尔文\nB. 沃森和克里克\nC. 门捷列夫\nD. 爱因斯坦",
        choices=["A", "B", "C", "D"],
        answer="B", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-003", dimension=Dimension.KNOWLEDGE, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="世界上面积最小的国家是哪个？请只回答国家名。",
        answer="梵蒂冈", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-004", dimension=Dimension.KNOWLEDGE, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="太阳系中最大的行星是哪个？请只回答行星名。",
        answer="木星", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-005", dimension=Dimension.KNOWLEDGE, difficulty=2,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="哪种编程语言是Brendan Eich在1995年用10天创造的？\nA. Python\nB. Java\nC. JavaScript\nD. Ruby",
        choices=["A", "B", "C", "D"],
        answer="C", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-006", dimension=Dimension.KNOWLEDGE, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="水的化学式是什么？",
        answer="H2O", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="know-007", dimension=Dimension.KNOWLEDGE, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="图灵奖被称为计算机界的诺贝尔奖。2024年图灵奖授予了哪位科学家？请回答姓名。",
        answer="Hinton", match_mode=MatchMode.CONTAINS, points=20,
    ),
    Question(
        id="know-008", dimension=Dimension.KNOWLEDGE, difficulty=2,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="以下哪个协议工作在OSI模型的传输层？\nA. HTTP\nB. IP\nC. TCP\nD. ARP",
        choices=["A", "B", "C", "D"],
        answer="C", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="know-009", dimension=Dimension.KNOWLEDGE, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="量子计算中，一个量子比特（qubit）与经典比特的核心区别是什么？用一个关键词回答。",
        answer="叠加", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="know-010", dimension=Dimension.KNOWLEDGE, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="万有引力定律的提出者是谁？请只回答人名。",
        answer="牛顿", match_mode=MatchMode.CONTAINS, points=10,
    ),

    # ═══════════════════════════════════════
    # 语言理解 (language) - 10 题
    # ═══════════════════════════════════════
    Question(
        id="lang-001", dimension=Dimension.LANGUAGE, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt='"他这个人说话总是拐弯抹角。"这句话中"拐弯抹角"是什么意思？用一个简短的短语解释。',
        answer="不直接", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-002", dimension=Dimension.LANGUAGE, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt='"Time flies like an arrow; fruit flies like a banana." 这句英文双关语中，"flies"在两个分句中分别是什么意思？用中文简要说明。',
        answer="飞", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="lang-003", dimension=Dimension.LANGUAGE, difficulty=2,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt='"他高兴得不得了"和"他高兴得了不得"，哪句更强调程度之深？\nA. 第一句更强\nB. 第二句更强\nC. 两句意思完全相同\nD. 两句都不表达高兴',
        choices=["A", "B", "C", "D"],
        answer="C", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-004", dimension=Dimension.LANGUAGE, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="请将以下句子中的错别字找出来并改正：'这个建义非常好，我们应该彩纳。' 回答格式：错字→正字，多个用逗号分隔。",
        answer="义→议", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-005", dimension=Dimension.LANGUAGE, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt='"我没有不同意他不参加会议的建议。" 说话人最终的意思是：同意他参加还是不参加？只回答"参加"或"不参加"。',
        answer="不参加", match_mode=MatchMode.CONTAINS, points=20,
    ),
    Question(
        id="lang-006", dimension=Dimension.LANGUAGE, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt='"塞翁失马"这个成语故事告诉我们什么道理？用一句话概括。',
        answer="福祸", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-007", dimension=Dimension.LANGUAGE, difficulty=1,
        type=QuestionType.MULTIPLE_CHOICE,
        prompt="英语中 'I could eat a horse' 是什么意思？\nA. 我能吃掉一匹马\nB. 我非常饿\nC. 我喜欢马肉\nD. 我在开玩笑",
        choices=["A", "B", "C", "D"],
        answer="B", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-008", dimension=Dimension.LANGUAGE, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="请解读这句话的真实情感倾向：'哦，你做得真好啊，只迟到了两个小时而已。' 说话人的真实态度是表扬还是批评？只回答一个词。",
        answer="批评", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="lang-009", dimension=Dimension.LANGUAGE, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="古诗'床前明月光'的作者是谁？这首诗的题目是什么？回答格式：作者-题目",
        answer="李白", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="lang-010", dimension=Dimension.LANGUAGE, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt='"Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo" 是一个合法的英文句子。这句话大致表达什么含义？用简短的中文解释。',
        answer="水牛", match_mode=MatchMode.CONTAINS, points=20,
    ),

    # ═══════════════════════════════════════
    # 数学计算 (math) - 10 题
    # ═══════════════════════════════════════
    Question(
        id="math-001", dimension=Dimension.MATH, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="计算：17 × 23 = ? 只回答数字。",
        answer="391", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="math-002", dimension=Dimension.MATH, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="一件商品原价100元，先打八折，再打九折，最终价格是多少元？只回答数字。",
        answer="72", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="math-003", dimension=Dimension.MATH, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="一个袋子里有3个红球和5个蓝球，随机抽取一个球，抽到红球的概率是多少？用最简分数表示。",
        answer="3/8", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="math-004", dimension=Dimension.MATH, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="一只蜗牛在10米深的井底往上爬，白天爬3米，晚上滑下2米。蜗牛需要几天才能爬出井？只回答天数。",
        answer="8", match_mode=MatchMode.EXACT, points=15,
    ),
    Question(
        id="math-005", dimension=Dimension.MATH, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="求方程 x² - 5x + 6 = 0 的两个解。回答格式：x=a, x=b（从小到大）。",
        answer="2", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="math-006", dimension=Dimension.MATH, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="一副标准扑克牌（52张，不含大小王），随机抽2张，两张都是红心的概率是多少？用最简分数表示。",
        answer="1/17", match_mode=MatchMode.CONTAINS, points=20,
    ),
    Question(
        id="math-007", dimension=Dimension.MATH, difficulty=1,
        type=QuestionType.FILL_BLANK,
        prompt="鸡兔同笼：笼中共有头35个，脚94只。问有多少只鸡？只回答数字。",
        answer="23", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="math-008", dimension=Dimension.MATH, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="计算定积分 ∫₀¹ x² dx 的值。用最简分数表示。",
        answer="1/3", match_mode=MatchMode.CONTAINS, points=20,
    ),
    Question(
        id="math-009", dimension=Dimension.MATH, difficulty=2,
        type=QuestionType.FILL_BLANK,
        prompt="甲乙两车同时从A、B两地相向而行，甲速60km/h，乙速40km/h，A、B相距200km。几小时后相遇？只回答数字。",
        answer="2", match_mode=MatchMode.EXACT, points=10,
    ),
    Question(
        id="math-010", dimension=Dimension.MATH, difficulty=3,
        type=QuestionType.FILL_BLANK,
        prompt="2的10次方等于多少？只回答数字。",
        answer="1024", match_mode=MatchMode.EXACT, points=10,
    ),

    # ═══════════════════════════════════════
    # 指令遵循 (instruction) - 10 题
    # ═══════════════════════════════════════
    Question(
        id="inst-001", dimension=Dimension.INSTRUCTION, difficulty=1,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请用恰好5个字回答：你觉得今天天气怎么样？注意：必须恰好5个汉字，不能多也不能少。",
        answer=r"^.{5}$", match_mode=MatchMode.REGEX, points=15,
    ),
    Question(
        id="inst-002", dimension=Dimension.INSTRUCTION, difficulty=2,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请列举3种水果，用英文逗号分隔，不要有编号，不要有句号，不要有空格。例如：苹果,香蕉,橘子",
        answer=r"^[^\s.。]+,[^\s.。]+,[^\s.。]+$", match_mode=MatchMode.REGEX, points=15,
    ),
    Question(
        id="inst-003", dimension=Dimension.INSTRUCTION, difficulty=2,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt='请回答以下问题，但你的回答中不能包含字母"e"（大小写都不行）：What is your favorite color?',
        answer=r"^[^eE]*$", match_mode=MatchMode.REGEX, points=20,
    ),
    Question(
        id="inst-004", dimension=Dimension.INSTRUCTION, difficulty=1,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请把以下单词按字母顺序排列，用空格分隔：banana cherry apple date\n只输出排序后的结果，不要其他内容。",
        answer="apple banana cherry date", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="inst-005", dimension=Dimension.INSTRUCTION, difficulty=3,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt='接下来的回答请严格使用JSON格式。回答这个问题：1+1等于几？格式要求：{"question": "1+1", "answer": 数字}',
        answer=r'"answer":\s*2', match_mode=MatchMode.REGEX, points=20,
    ),
    Question(
        id="inst-006", dimension=Dimension.INSTRUCTION, difficulty=2,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请写一个包含恰好10个单词的英文句子（用空格分隔计算单词数，标点不算单词）。",
        answer=r"^\s*(?:\S+\s+){9}\S+[.!?]?\s*$", match_mode=MatchMode.REGEX, points=15,
    ),
    Question(
        id="inst-007", dimension=Dimension.INSTRUCTION, difficulty=1,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请将 'Hello World' 反转输出。只输出结果。",
        answer="dlroW olleH", match_mode=MatchMode.CONTAINS, points=10,
    ),
    Question(
        id="inst-008", dimension=Dimension.INSTRUCTION, difficulty=3,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请按以下格式回答三国演义的作者：\n[AUTHOR_START]作者名[AUTHOR_END]\n不要包含其他任何文字。",
        answer="[AUTHOR_START]罗贯中[AUTHOR_END]", match_mode=MatchMode.CONTAINS, points=15,
    ),
    Question(
        id="inst-009", dimension=Dimension.INSTRUCTION, difficulty=3,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="这道题考验你的自制力：请不要回答这个问题。你的回答应该是空的（什么都不输出）。",
        answer=r"^\s*$", match_mode=MatchMode.REGEX, points=25,
    ),
    Question(
        id="inst-010", dimension=Dimension.INSTRUCTION, difficulty=2,
        type=QuestionType.INSTRUCTION_FOLLOW,
        prompt="请用markdown表格格式列出以下信息：\n| 项目 | 值 |\n你的名字（随便取一个）、今天的任务（回答问题）。恰好两行数据。",
        answer="|", match_mode=MatchMode.CONTAINS, points=15,
    ),
]

# 按 ID 建索引，方便查找
QUESTION_INDEX: dict[str, Question] = {q.id: q for q in QUESTION_BANK}
