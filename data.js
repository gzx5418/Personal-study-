// 模拟课程数据
const courses = [
    {
        id: 1,
        name: '人工智能导论',
        icon: 'fas fa-brain',
        progress: 65,
        totalChapters: 12,
        completedChapters: 8
    },
    {
        id: 2,
        name: 'Python编程基础',
        icon: 'fas fa-code',
        progress: 80,
        totalChapters: 10,
        completedChapters: 8
    },
    {
        id: 3,
        name: '机器学习算法',
        icon: 'fas fa-network-wired',
        progress: 45,
        totalChapters: 15,
        completedChapters: 7
    },
    {
        id: 4,
        name: '数据结构与算法',
        icon: 'fas fa-database',
        progress: 70,
        totalChapters: 14,
        completedChapters: 10
    }
];

// 模拟学习资源数据
const resources = [
    {
        id: 1,
        type: 'document',
        title: '深度学习入门指南',
        description: '全面介绍深度学习基本概念和原理',
        date: '2024-01-15',
        views: 328,
        icon: 'fas fa-file-pdf'
    },
    {
        id: 2,
        type: 'video',
        title: '神经网络结构可视化',
        description: '多模态动画展示神经网络工作原理',
        date: '2024-01-14',
        views: 512,
        icon: 'fas fa-video'
    },
    {
        id: 3,
        type: 'quiz',
        title: '神经网络基础测验',
        description: '包含20道精选选择题和填空题',
        date: '2024-01-13',
        participants: 189,
        icon: 'fas fa-clipboard-list'
    },
    {
        id: 4,
        type: 'code',
        title: 'MNIST手写数字识别',
        description: '完整的PyTorch实现代码和注释',
        date: '2024-01-12',
        downloads: 256,
        icon: 'fas fa-code'
    },
    {
        id: 5,
        type: 'document',
        title: '卷积神经网络详解',
        description: '深入理解CNN的原理和应用',
        date: '2024-01-11',
        views: 445,
        icon: 'fas fa-file-text'
    },
    {
        id: 6,
        type: 'video',
        title: '反向传播算法动画',
        description: '直观展示梯度下降和反向传播过程',
        date: '2024-01-10',
        views: 678,
        icon: 'fas fa-play-circle'
    }
];

// 模拟学习画像数据
const userProfile = {
    knowledgeBase: {
        math: 90,
        programming: 75,
        machineLearning: 65,
        statistics: 82,
        dataAnalysis: 78
    },
    cognitiveStyle: ['视觉型学习者', '逻辑推理强', '实践导向', '自主学习'],
    weakPoints: ['反向传播算法', '正则化技巧', '模型调优'],
    learningStats: {
        mastery: 85,
        activity: 68,
        totalHours: 120,
        accuracy: 92
    }
};

// 模拟学习路径数据
const learningPath = {
    goal: '掌握深度学习核心技术，能够独立完成简单的机器学习项目',
    duration: '12周',
    currentStage: '第三阶段：神经网络进阶',
    stages: [
        {
            id: 1,
            name: '第一阶段：基础准备',
            description: '数学基础、Python编程、线性代数复习',
            status: 'completed'
        },
        {
            id: 2,
            name: '第二阶段：机器学习基础',
            description: '监督学习、无监督学习、评估指标',
            status: 'completed'
        },
        {
            id: 3,
            name: '第三阶段：神经网络进阶',
            description: '深度学习架构、CNN、RNN、Transformer',
            status: 'current'
        },
        {
            id: 4,
            name: '第四阶段：实践项目',
            description: '完整项目实战、模型调优、部署上线',
            status: 'pending'
        },
        {
            id: 5,
            name: '第五阶段：进阶专题',
            description: '强化学习、生成模型、多模态学习',
            status: 'pending'
        }
    ]
};

// 模拟智能对话数据
const chatResponses = {
    default: [
        '好的，我来帮您解答这个问题。根据您的学习画像，我会为您提供个性化的解答。',
        '这是一个很好的问题！让我为您详细解释一下...',
        '根据您的学习进度，我为您推荐以下学习资源：',
        '我理解您的疑问，让我用更简单的方式为您解释...',
        '这个知识点确实比较复杂，让我为您分解一下...',
        '好的，我来帮您生成相关的学习材料...',
        '根据您的易错点分析，我建议您重点关注这部分内容...'
    ],
    neuralNetwork: '神经网络是一种模仿生物神经网络结构和功能的计算模型。它由大量的神经元（节点）相互连接组成，通过学习数据模式来进行预测和决策。主要包括输入层、隐藏层和输出层。',
    backpropagation: '反向传播算法是训练神经网络的核心方法。它通过计算预测值与真实值之间的误差，然后从输出层反向传播到输入层，利用梯度下降法更新网络权重，从而最小化误差。',
    deepLearning: '深度学习是机器学习的一个分支，使用深层神经网络来学习数据的复杂特征表示。它在图像识别、自然语言处理、语音识别等领域取得了革命性的突破。',
    cnn: '卷积神经网络（CNN）是一种专门用于处理网格数据（如图像）的深度学习模型。它通过卷积层、池化层等结构自动提取图像特征，在计算机视觉任务中表现出色。',
    learningPath: '根据您的学习画像，我已经为您规划了个性化的学习路径。当前您正在第三阶段：神经网络进阶。建议您先巩固CNN的基础知识，然后再学习RNN和Transformer。',
    resource: '根据您的学习进度，我为您推荐以下资源：\n\n1. 《深度学习入门指南》文档\n2. 神经网络结构可视化视频\n3. CNN基础测验题库\n4. PyTorch实践代码案例',
    help: '我可以帮您解答关于课程内容的问题，生成学习资源，规划学习路径等。请问有什么我可以帮助您的吗？'
};

// 导出数据
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        courses,
        resources,
        userProfile,
        learningPath,
        chatResponses
    };
}