package com.duochouchou.joytrunk.ui.locale

import androidx.compose.runtime.compositionLocalOf

/** 当前应用语言，用于 UI 字符串切换 */
val LocalAppLanguage = compositionLocalOf<String> { "zh" }

/** 根据当前语言返回多语言文案 */
object AppStrings {
    private val zh = mapOf(
        // Tabs / common
        "tab_chat" to "聊天",
        "tab_overview" to "概览",
        "tab_token" to "Token",
        "tab_settings" to "设置",
        "loading" to "加载中...",
        "copied" to "已复制",

        // Chat
        "session" to "会话",
        "input_message" to "输入消息",
        "send" to "发送",
        "new_conversation" to "新会话",
        "select_employee" to "选择员工",
        "create_conversation" to "创建会话",
        "creating" to "创建中...",
        "no_employee_hint" to "暂无可用员工，请先在电脑端绑定 JoyTrunk CLI。",

        // Overview
        "overview" to "概览",
        "cli_employees" to "CLI 员工",
        "user_fallback" to "用户",

        // Token
        "token" to "Token",
        "token_usage" to "Token 用量",
        "balance" to "余额",
        "quota" to "额度",
        "api_key" to "API Key",
        "not_generated" to "未生成",
        "generate_api_key" to "生成 API Key",
        "hide" to "隐藏",
        "regen_hint" to "重新生成后可复制完整Key",
        "copy" to "复制",

        // Auth / login
        "login_subtitle" to "登录以继续",
        "login_tab_phone" to "手机",
        "login_tab_email" to "邮箱",
        "login_tab_password" to "密码",
        "login_phone" to "手机号",
        "login_email" to "邮箱",
        "login_code" to "验证码",
        "login_account" to "账号",
        "login_password" to "密码",
        "login_send_code" to "发送验证码",
        "login" to "登录",
        "go_to_register" to "去注册",
        "email_register_hint" to "新用户输入邮箱获取验证码即完成注册",

        // Chat think blocks
        "think_expand" to "展开思考过程",
        "think_collapse" to "收起思考过程",
        "show_password" to "显示密码",
        "hide_password" to "隐藏密码",

        "settings" to "设置",
        "profile" to "资料",
        "language" to "语言",
        "theme" to "主题",
        "password" to "密码",
        "logout" to "退出登录",
        "language_zh" to "简体中文",
        "language_en" to "English",
        "theme_dark" to "深色模式",
        "nickname" to "昵称",
        "avatar_url" to "头像 URL",
        "save" to "保存",
        "current_password" to "当前密码",
        "new_password" to "新密码",
        "change_password" to "修改密码",
        "password_changed" to "密码已修改",
        "saved" to "已保存",
        "back" to "返回",
    )

    private val en = mapOf(
        // Tabs / common
        "tab_chat" to "Chat",
        "tab_overview" to "Overview",
        "tab_token" to "Token",
        "tab_settings" to "Settings",
        "loading" to "Loading...",
        "copied" to "Copied",

        // Chat
        "session" to "Session",
        "input_message" to "Type a message",
        "send" to "Send",
        "new_conversation" to "New chat",
        "select_employee" to "Select employee",
        "create_conversation" to "Create chat",
        "creating" to "Creating...",
        "no_employee_hint" to "No employees available. Please bind JoyTrunk CLI on desktop first.",

        // Overview
        "overview" to "Overview",
        "cli_employees" to "CLI employees",
        "user_fallback" to "User",

        // Token
        "token" to "Token",
        "token_usage" to "Token usage",
        "balance" to "Balance",
        "quota" to "Quota",
        "api_key" to "API Key",
        "not_generated" to "Not generated",
        "generate_api_key" to "Generate API Key",
        "hide" to "Hide",
        "regen_hint" to "Regenerate to copy full key",
        "copy" to "Copy",

        // Auth / login
        "login_subtitle" to "Sign in to continue",
        "login_tab_phone" to "Phone",
        "login_tab_email" to "Email",
        "login_tab_password" to "Password",
        "login_phone" to "Phone",
        "login_email" to "Email",
        "login_code" to "Code",
        "login_account" to "Account",
        "login_password" to "Password",
        "login_send_code" to "Send code",
        "login" to "Sign in",
        "go_to_register" to "Go to register",
        "email_register_hint" to "New users can register with email code",

        // Chat think blocks
        "think_expand" to "Show reasoning",
        "think_collapse" to "Hide reasoning",
        "show_password" to "Show password",
        "hide_password" to "Hide password",

        "settings" to "Settings",
        "profile" to "Profile",
        "language" to "Language",
        "theme" to "Theme",
        "password" to "Password",
        "logout" to "Log out",
        "language_zh" to "简体中文",
        "language_en" to "English",
        "theme_dark" to "Dark mode",
        "nickname" to "Nickname",
        "avatar_url" to "Avatar URL",
        "save" to "Save",
        "current_password" to "Current password",
        "new_password" to "New password",
        "change_password" to "Change password",
        "password_changed" to "Password changed",
        "saved" to "Saved",
        "back" to "Back",
    )

    fun get(lang: String, key: String): String {
        val map = if (lang == "en") en else zh
        return map[key] ?: zh[key] ?: key
    }
}
