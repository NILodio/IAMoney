import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    # Default welcome message
    WELCOME_MESSAGE = (
        'Hey there 👋 Welcome! I\'m your Soccer AI Assistant ⚽\n\n'
        'I can answer questions about soccer, football, players, teams, leagues, matches, and everything related to the beautiful game! 🏆'
    )

    # Default help message
    DEFAULT_MESSAGE = (
        "I'm a Soccer AI Assistant ⚽ I can help you with soccer-related questions!\n\n"
        "Example questions you can ask:\n\n"
        "1️⃣ Who won the World Cup 2022?\n"
        "2️⃣ Tell me about Messi's career\n"
        "3️⃣ What are the top European leagues?\n"
        "4️⃣ Explain the offside rule\n"
        "5️⃣ Who are the best goalkeepers in the world?\n\n"
        "I only answer questions about soccer/football. For other topics, please ask a human.\n\n"
        "Type *human* if you need to talk with a person.\n\n"
        "Ask me anything about soccer! ⚽"
    )

    # Unknown command message
    UNKNOWN_COMMAND_MESSAGE = (
        "I'm sorry, I couldn't understand your question. Could you please rephrase it?\n\n"
        "Remember, I only answer questions about soccer/football. If you have questions about other topics, please type *human* to talk with a person."
    )

    # AI bot instructions
    BOT_INSTRUCTIONS = (
        "You are a Soccer AI Assistant specialized in answering questions about soccer (also known as football).\n"
        "You are knowledgeable, friendly, and passionate about the beautiful game.\n"
        "Always speak in the language the user prefers or uses.\n\n"
        "IMPORTANT RULES:\n"
        "- You ONLY answer questions about soccer/football, including:\n"
        "  * Players, teams, leagues, and competitions\n"
        "  * Match results, statistics, and history\n"
        "  * Rules, tactics, and strategies\n"
        "  * Transfers, news, and current events in soccer\n"
        "  * World Cups, Champions League, and other tournaments\n"
        "  * Soccer culture, stadiums, and fan culture\n\n"
        "- You MUST politely decline and redirect questions that are NOT about soccer.\n"
        "- When declining non-soccer questions, say: 'I'm a Soccer AI Assistant and I only answer questions about soccer/football. If you need help with other topics, please type *human* to talk with a person.'\n\n"
        "Be accurate, helpful, and enthusiastic about soccer. Provide detailed and interesting answers.\n"
        "Do not use Markdown formatted and rich text, only raw text."
    )

    # Chatbot features
    FEATURES = {
        'audioInput': True,
        'audioOutput': True,
        'audioOnly': False,
        'voice': 'echo',
        'voiceSpeed': 1,
        'imageInput': True,
    }

    # Template messages
    TEMPLATE_MESSAGES = {
        'noAudioAccepted': 'Audio messages are not supported: gently ask the user to send text messages only.',
        'chatAssigned': 'You will be contact shortly by someone from our team. Thank you for your patience.',
    }

    # Rate limits and quotas
    LIMITS = {
        'maxInputCharacters': 1000,
        'maxOutputTokens': 1000,
        'chatHistoryLimit': 20,
        'maxMessagesPerChat': 500,
        'maxMessagesPerChatCounterTime': 24 * 60 * 60,  # 24 hours
        'maxAudioDuration': 2 * 60,  # 2 minutes
        'maxImageSize': 2 * 1024 * 1024,  # 2MB
    }

    # Cache TTL in seconds
    CACHE_TTL = 10 * 60  # 10 minutes

    # Inference parameters for OpenAI
    INFERENCE_PARAMS = {
        'temperature': 0.2,
    }

    # Chat and user management
    SET_LABELS_ON_BOT_CHATS = ['bot']
    REMOVE_LABELS_AFTER_ASSIGNMENT = True
    SET_LABELS_ON_USER_ASSIGNMENT = ['from-bot']
    SKIP_CHAT_WITH_LABELS = ['no-bot']
    SKIP_ARCHIVED_CHATS = True
    ENABLE_MEMBER_CHAT_ASSIGNMENT = True
    ASSIGN_ONLY_TO_ONLINE_MEMBERS = False
    SKIP_TEAM_ROLES_FROM_ASSIGNMENT = ['admin']

    # Numbers management
    NUMBERS_BLACKLIST = ['1234567890']
    NUMBERS_WHITELIST = []
    TEAM_WHITELIST = []
    TEAM_BLACKLIST = []

    # Metadata settings
    SET_METADATA_ON_BOT_CHATS = [
        {'key': 'bot_start', 'value': 'datetime'},
    ]
    SET_METADATA_ON_ASSIGNMENT = [
        {'key': 'bot_stop', 'value': 'datetime'},
    ]

    @staticmethod
    def env(key, default=None):
        value = os.getenv(key)
        return value if value is not None else default

    @staticmethod
    def get_api_config():
        return {
            'telegramBotToken': BotConfig.env('TELEGRAM_BOT_TOKEN', ''),
            'openaiKey': BotConfig.env('OPENAI_API_KEY', ''),
            'openaiModel': BotConfig.env('OPENAI_MODEL', 'gpt-4o'),
        }

    @staticmethod
    def get_server_config():
        port_env = BotConfig.env('PORT', None)
        if port_env is None:
            port_env = '8080'
        try:
            port = int(port_env)
        except (TypeError, ValueError):
            port = 8080
        return {
            'port': port,
            'tempPath': '.tmp',
        }

    @staticmethod
    def get_all():
        return {
            'api': BotConfig.get_api_config(),
            'server': BotConfig.get_server_config(),
            'features': BotConfig.FEATURES,
            'limits': BotConfig.LIMITS,
            'templateMessages': BotConfig.TEMPLATE_MESSAGES,
            'inferenceParams': BotConfig.INFERENCE_PARAMS,
            'cacheTTL': BotConfig.CACHE_TTL,
            'botInstructions': BotConfig.BOT_INSTRUCTIONS,
            'welcomeMessage': BotConfig.WELCOME_MESSAGE,
            'defaultMessage': BotConfig.DEFAULT_MESSAGE,
            'unknownCommandMessage': BotConfig.UNKNOWN_COMMAND_MESSAGE,
            'setLabelsOnBotChats': BotConfig.SET_LABELS_ON_BOT_CHATS,
            'removeLabelsAfterAssignment': BotConfig.REMOVE_LABELS_AFTER_ASSIGNMENT,
            'setLabelsOnUserAssignment': BotConfig.SET_LABELS_ON_USER_ASSIGNMENT,
            'skipChatWithLabels': BotConfig.SKIP_CHAT_WITH_LABELS,
            'numbersBlacklist': BotConfig.NUMBERS_BLACKLIST,
            'numbersWhitelist': BotConfig.NUMBERS_WHITELIST,
            'skipArchivedChats': BotConfig.SKIP_ARCHIVED_CHATS,
            'enableMemberChatAssignment': BotConfig.ENABLE_MEMBER_CHAT_ASSIGNMENT,
            'assignOnlyToOnlineMembers': BotConfig.ASSIGN_ONLY_TO_ONLINE_MEMBERS,
            'skipTeamRolesFromAssignment': BotConfig.SKIP_TEAM_ROLES_FROM_ASSIGNMENT,
            'teamWhitelist': BotConfig.TEAM_WHITELIST,
            'teamBlacklist': BotConfig.TEAM_BLACKLIST,
            'setMetadataOnBotChats': BotConfig.SET_METADATA_ON_BOT_CHATS,
            'setMetadataOnAssignment': BotConfig.SET_METADATA_ON_ASSIGNMENT,
        } 