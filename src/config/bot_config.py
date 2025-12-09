import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    # Default welcome message
    WELCOME_MESSAGE = (
        'Hey there 👋 Welcome to this ChatGPT-powered AI chatbot demo using *Wassenger API*! I can also speak many languages 😁'
    )

    # Default help message
    DEFAULT_MESSAGE = (
        "Don't be shy 😁 try asking anything to the AI chatbot, using natural language!\n\n"
        "Example queries:\n\n"
        "1️⃣ Explain me what is Wassenger\n"
        "2️⃣ Can I use Wassenger to send automatic messages?\n"
        "3️⃣ Can I schedule messages using Wassenger?\n"
        "4️⃣ Is there a free trial available?\n\n"
        "Type *human* to talk with a person. The chat will be assigned to an available member of the team.\n\n"
        "Give it a try! 😁"
    )

    # Unknown command message
    UNKNOWN_COMMAND_MESSAGE = (
        "I'm sorry, I was unable to understand your message. Can you please elaborate more?\n\n"
        "If you would like to chat with a human, just reply with *human*."
    )

    # AI bot instructions
    BOT_INSTRUCTIONS = (
        "You are a smart virtual customer support assistant who works for Wassenger.\n"
        "You can identify yourself as Milo, the Wassenger AI Assistant.\n"
        "You will be chatting with random customers who may contact you with general queries about the product.\n"
        "Wassenger is a cloud solution that offers WhatsApp API and multi-user live communication services designed for businesses and developers.\n"
        "Wassenger also enables customers to automate WhatsApp communication and build chatbots.\n"
        "You are an expert customer support agent.\n"
        "Be polite. Be helpful. Be emphatic. Be concise.\n"
        "Politely reject any queries that are not related to customer support tasks or Wassenger services itself.\n"
        "Stick strictly to your role as a customer support virtual assistant for Wassenger.\n"
        "Always speak in the language the user prefers or uses.\n"
        "If you can't help with something, ask the user to type *human* in order to talk with customer support.\n"
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
            'apiKey': BotConfig.env('API_KEY', 'ENTER API KEY HERE'),
            'openaiKey': BotConfig.env('OPENAI_API_KEY', ''),
            'openaiModel': BotConfig.env('OPENAI_MODEL', 'gpt-4o'),
            'apiBaseUrl': BotConfig.env('API_URL', 'https://api.wassenger.com/v1'),
            'device': BotConfig.env('DEVICE', 'ENTER WHATSAPP DEVICE ID'),
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
            'webhookUrl': BotConfig.env('WEBHOOK_URL'),
            'ngrokToken': BotConfig.env('NGROK_TOKEN', ''),
            'ngrokPath': BotConfig.env('NGROK_PATH'),
            'production': BotConfig.env('NODE_ENV') == 'production',
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