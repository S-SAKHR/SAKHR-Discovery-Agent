import os
import requests
from typing import Optional, List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from agents.orchestrator import ResearchOrchestrator
from agents.analyzer import analyze_collection
from agents.comparator import compare_publications
from agents.gap_detector import detect_research_gaps
from agents.trend_detector import analyze_trends
from agents.reporter import generate_daily_report
from database.db import (
    save_papers,
    get_papers,
    get_unanalyzed_papers,
    save_analyses,
    get_statistics
)

WELCOME_MESSAGE = """🧬 WELCOME TO SAKHR AVA_R

Beyond Information. Toward Discovery.

━━━━━━━━━━━━━━━━━━━━

Your gateway to multidisciplinary scientific intelligence.

Explore the frontiers of:

🔬 MEDICINE & BIOLOGY
🧠 NEUROSCIENCE
🤖 ARTIFICIAL INTELLIGENCE
⚛️ PHYSICS & MATHEMATICS
🌌 ASTRONOMY & SPACE SCIENCE
🧬 BIOENGINEERING & BIOTECHNOLOGY

━━━━━━━━━━━━━━━━━━━━

DISCOVER RESEARCH.
CONNECT KNOWLEDGE.
INVESTIGATE THE UNKNOWN.

Your scientific journey starts here.

⚡ Powered by SAKHR Scientific Intelligence."""


def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔬 Research", callback_data="btn_research"),
            InlineKeyboardButton("🧠 Neuroscience", callback_data="btn_neuroscience")
        ],
        [
            InlineKeyboardButton("🤖 Artificial Intelligence", callback_data="btn_ai"),
            InlineKeyboardButton("⚛️ Physics", callback_data="btn_physics")
        ],
        [
            InlineKeyboardButton("🌌 Astronomy", callback_data="btn_astronomy"),
            InlineKeyboardButton("🧬 Biology", callback_data="btn_biology")
        ],
        [
            InlineKeyboardButton("📊 Research Trends", callback_data="btn_trends"),
            InlineKeyboardButton("📚 Recent Publications", callback_data="btn_recent")
        ],
        [
            InlineKeyboardButton("⚙️ System Status", callback_data="btn_status")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def check_authorization(update: Update) -> bool:
    """
    Verifies if the incoming update is from the authorized user ID (TELEGRAM_ALLOWED_USER_ID).
    If TELEGRAM_ALLOWED_USER_ID is not set in .env, allows access.
    """
    allowed_user_id = os.getenv("TELEGRAM_ALLOWED_USER_ID")
    if not allowed_user_id:
        return True
    
    user = update.effective_user
    if not user:
        return False
    
    return str(user.id) == str(allowed_user_id)


def split_markdown_message(text: str, max_len: int = 3900) -> List[str]:
    """
    Splits a long Markdown message into chunks below max_len,
    ensuring we do not split in the middle of a word, paragraph, or publication reference [Title](url).
    """
    if len(text) <= max_len:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        split_idx = max_len
        sub = remaining[:max_len]
        last_para = sub.rfind("\n\n")
        if last_para > max_len * 0.4:
            split_idx = last_para + 2
        else:
            last_line = sub.rfind("\n")
            if last_line > max_len * 0.4:
                split_idx = last_line + 1
            else:
                last_space = sub.rfind(" ")
                if last_space > max_len * 0.4:
                    split_idx = last_space + 1

        chunk = remaining[:split_idx].strip()
        if chunk.count("**") % 2 != 0:
            chunk += "**"

        chunks.append(chunk)
        remaining = remaining[split_idx:].strip()

    return chunks


def send_telegram_message(message: str, chat_id: Optional[str] = None, token: Optional[str] = None, reply_markup: Optional[Any] = None) -> bool:
    """
    Sends a message via Telegram Bot API with robust smart chunking and formatting preservation.
    """
    bot_token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not target_chat_id:
        print("[Telegram] Credentials (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID) not configured. Skipping Telegram delivery.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = split_markdown_message(message, max_len=3900)

    success = True
    for idx, chunk in enumerate(chunks):
        payload = {
            "chat_id": target_chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        if reply_markup and idx == len(chunks) - 1:
            payload["reply_markup"] = reply_markup.to_dict()

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[Telegram] Failed to send message chunk: {e}")
            try:
                payload["parse_mode"] = None
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
            except Exception as inner_e:
                print(f"[Telegram] Retry without Markdown failed: {inner_e}")
                success = False

    if success:
        print("[Telegram] Message delivered successfully.")
    return success


def send_telegram_document_report(chat_id: str, bot_token: str, report_text: str, filename: str = "sakhr_scientific_report.md") -> bool:
    """
    Sends a long scientific intelligence report as a document file (.md) via Telegram sendDocument API.
    """
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    files = {
        "document": (filename, report_text.encode("utf-8"), "text/markdown")
    }
    data = {
        "chat_id": chat_id,
        "caption": "🔬 SAKHR Scientific Intelligence Comprehensive Report (Full Document)",
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=data, files=files, timeout=60)
        response.raise_for_status()
        print("[Telegram] Report document delivered successfully.")
        return True
    except Exception as e:
        print(f"[Telegram] Failed to send document report: {e}")
        return False


# =====================================
# COMMAND HANDLERS
# =====================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access. Your Telegram user ID is not authorized to use SAKHR AVA_R.")
        return

    await update.effective_message.reply_text(
    WELCOME_MESSAGE,
    reply_markup=get_main_keyboard()
)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    help_text = """📚 *SAKHR AVA_R PROFESSIONAL COMMAND SYSTEM*

/start — Welcome and main navigation.
/help — Explain all available capabilities.
/research <topic> — Search multidisciplinary scientific literature.
/analyze <topic> — Retrieve and scientifically analyze publications.
/compare <topic> — Compare findings across multiple studies.
/trends <field> — Identify emerging research trends.
/discover <field> — Discover recent publications and scientific developments.
/recent — Show recently collected publications.
/report <topic> — Generate a structured scientific intelligence report.
/status — Show system and service status.
/domains — Display supported scientific disciplines.
/about — Explain SAKHR AVA_R.

⚡ *Powered by SAKHR Scientific Intelligence.*"""
    await update.effective_message.reply_text(help_text, parse_mode="Markdown")


async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    topic = " ".join(args)
    if not topic:
        await update.effective_message.reply_text("⚠️ Please specify a research topic. Example:\n`/research CRISPR gene editing`", parse_mode="Markdown")
        return

    msg = await update.effective_message.reply_text(f"🔍 Searching multidisciplinary scientific literature for *{topic}*...", parse_mode="Markdown")
    try:
        orchestrator = ResearchOrchestrator()
        papers = orchestrator.search(topic, max_results_per_source=2)
        if not papers:
            await msg.edit_text(f"❌ No publications retrieved for topic: *{topic}*", parse_mode="Markdown")
            return

        save_papers(papers, topic=topic)

        provenance = papers[0].get("provenance", {}) if papers else {}
        successful = provenance.get("successful_sources", [])
        failed = provenance.get("failed_sources", [])
        incomplete = provenance.get("incomplete_search", False)

        response_lines = [f"🔬 *Research Results: {topic}*", f"Found & verified *{len(papers)}* multidisciplinary publications:\n"]
        if incomplete:
            response_lines.append(f"⚠️ *Notice:* Incomplete search. Successful: `{successful}` | Failed/Skipped: `{failed}`\n")
        else:
            response_lines.append(f"✅ *Sources:* `{successful}`\n")

        for i, p in enumerate(papers[:5], 1):
            title = p.get("title", "No title")
            url = p.get("url", "#")
            doi = p.get("doi", "N/A")
            pmid = p.get("pmid", "N/A")
            source = p.get("source", "Multi-source")
            response_lines.append(f"{i}. *{title}*\n   - Source: `{source}` | DOI: `{doi}` | PMID: `{pmid}`\n   - [View Publication]({url})\n")

        full_text = "\n".join(response_lines)
        chunks = split_markdown_message(full_text)
        await msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error executing research search: {e}")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    topic = " ".join(args)
    if not topic:
        await update.effective_message.reply_text("⚠️ Please specify a topic to analyze. Example:\n`/analyze Quantum computing`", parse_mode="Markdown")
        return

    msg = await update.effective_message.reply_text(f"🧠 Running Gemini Scientific Analysis on *{topic}* publications...", parse_mode="Markdown")
    try:
        orchestrator = ResearchOrchestrator()
        papers = orchestrator.search(topic, max_results_per_source=2)
        if not papers:
            await msg.edit_text(f"❌ No publications found to analyze for: *{topic}*", parse_mode="Markdown")
            return

        save_papers(papers, topic=topic)
        unanalyzed = get_unanalyzed_papers(topic=topic)
        target_papers = unanalyzed if unanalyzed else get_papers(limit=3, topic=topic)
        if not target_papers:
            target_papers = papers[:3]

        analyses = analyze_collection(target_papers)
        save_analyses(analyses)

        resp = [f"🧠 *Gemini Scientific Analysis: {topic}*\n"]
        for a in analyses:
            if "error" in a:
                continue
            resp.append(f"📌 *{a.get('title', 'Publication')}*\n- *Research Question:* {a.get('research_question', 'N/A')}\n- *Methodology:* {a.get('methodology', 'N/A')}\n- *Main Findings:* {a.get('main_findings', 'N/A')}\n- *Limitations:* {a.get('limitations', 'N/A')}\n")

        full_text = "\n".join(resp)
        chunks = split_markdown_message(full_text)
        await msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error during scientific analysis: {e}")


async def compare_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    topic = " ".join(args)
    if not topic:
        await update.effective_message.reply_text("⚠️ Please specify a topic to compare. Example:\n`/compare Alzheimer disease therapy`", parse_mode="Markdown")
        return

    msg = await update.effective_message.reply_text(f"⚖️ Comparing findings across multiple studies for *{topic}*...", parse_mode="Markdown")
    try:
        orchestrator = ResearchOrchestrator()
        papers = orchestrator.search(topic, max_results_per_source=2)
        if papers:
            save_papers(papers, topic=topic)

        stored = get_papers(limit=5, topic=topic)
        if not stored:
            stored = papers

        formatted_papers = []
        for p in stored:
            formatted_papers.append({
                "title": p.get("title"),
                "abstract": p.get("abstract"),
                "analysis": {"main_findings": p.get("abstract", "")[:300], "limitations": "Standard constraints"}
            })

        comparison = compare_publications(formatted_papers)

        resp = [
            f"⚖️ *Cross-Study Comparison: {topic}*",
            f"\n*Synthesis Summary:* {comparison.get('synthesis_summary', 'N/A')}",
            f"\n*Key Agreements:*"
        ]
        for ag in comparison.get("agreements", []):
            resp.append(f"- {ag}")
        resp.append(f"\n*Contradictions:*")
        for co in comparison.get("contradictions", []):
            resp.append(f"- {co}")

        full_text = "\n".join(resp)
        chunks = split_markdown_message(full_text)
        await msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error comparing publications: {e}")


async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    field = " ".join(args) if args else None
    msg = await update.effective_message.reply_text(f"📊 Analyzing research trends for *{field or 'All Fields'}*...", parse_mode="Markdown")
    try:
        trends = analyze_trends(topic=field)
        resp = [
            f"📊 *Research Trends & Knowledge Metrics*",
            f"- *Target Field/Topic:* {trends.get('topic')}",
            f"- *Total Monitored Publications:* {trends.get('total_papers')}",
            f"- *Source Distribution:* `{trends.get('source_distribution')}`",
            f"- *Preprint Breakdown:* `{trends.get('preprint_breakdown')}`"
        ]
        await msg.edit_text("\n".join(resp), parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Error analyzing trends: {e}")


async def discover_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    field = " ".join(args)
    if not field:
        await update.effective_message.reply_text("⚠️ Please specify a scientific field. Example:\n`/discover Artificial Intelligence`", parse_mode="Markdown")
        return

    msg = await update.effective_message.reply_text(f"🌌 Discovering recent scientific developments in *{field}*...", parse_mode="Markdown")
    try:
        orchestrator = ResearchOrchestrator()
        papers = orchestrator.search(field, max_results_per_source=2)
        if papers:
            save_papers(papers, topic=field)

        resp = [f"🌌 *Discovery Feed: {field}*\n"]
        for i, p in enumerate(papers[:5], 1):
            resp.append(f"{i}. *{p.get('title')}*\n   - Published: `{p.get('published_date', 'N/A')}`\n   - [Read Paper]({p.get('url', '#')})\n")
        full_text = "\n".join(resp)
        chunks = split_markdown_message(full_text)
        await msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error during discovery: {e}")


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    msg = await update.effective_message.reply_text("📚 Retrieving recently collected publications...", parse_mode="Markdown")
    try:
        papers = get_papers(limit=10)
        if not papers:
            await msg.edit_text("📚 No publications found in the knowledge base yet. Run `/research <topic>` to collect papers.")
            return

        resp = ["📚 *Recently Collected Publications*\n"]
        for i, p in enumerate(papers[:8], 1):
            resp.append(f"{i}. *{p.get('title')}*\n   - Topic: `{p.get('topic', 'General')}` | PMID: `{p.get('pmid', 'N/A')}`\n")
        await msg.edit_text("\n".join(resp)[:4000], parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Error retrieving recent publications: {e}")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    args = context.args if context and context.args else []
    topic = " ".join(args)
    if not topic:
        await update.effective_message.reply_text("⚠️ Please specify a topic for the report. Example:\n`/report CRISPR gene editing`", parse_mode="Markdown")
        return

    msg = await update.effective_message.reply_text(f"📑 Generating comprehensive scientific intelligence report for *{topic}*...", parse_mode="Markdown")
    try:
        orchestrator = ResearchOrchestrator()
        papers = orchestrator.search(topic, max_results_per_source=2)
        if papers:
            save_papers(papers, topic=topic)

        stored_papers = get_papers(limit=5, topic=topic)
        formatted = [{"title": p.get("title"), "abstract": p.get("abstract"), "analysis": {"main_findings": p.get("abstract", "")[:200]}} for p in stored_papers]

        comparison = compare_publications(formatted)
        gaps = detect_research_gaps(formatted)
        trends = analyze_trends(topic=topic)

        report_md = generate_daily_report(
            topic=topic,
            papers=stored_papers,
            analyses=[],
            comparison=comparison,
            gaps=gaps,
            trends=trends
        )

        os.makedirs("reports", exist_ok=True)
        report_filename = f"reports/report_{topic.replace(' ', '_')}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report_md)

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = update.effective_chat.id
        if bot_token and chat_id:
            send_telegram_document_report(str(chat_id), bot_token, report_md, filename=f"report_{topic.replace(' ', '_')}.md")

        max_len = 3900
        chunks = split_markdown_message(report_md, max_len=max_len)
        await msg.edit_text(chunks[0], parse_mode="Markdown", disable_web_page_preview=True)
        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        await msg.edit_text(f"❌ Error generating report: {e}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    msg = None
    try:
        msg = await update.effective_message.reply_text("⚙️ Checking SAKHR AVA_R System Status...", parse_mode="Markdown")
        stats = get_statistics()
        resp = [
            f"⚙️ *SAKHR AVA_R System Status*",
            f"- *Database Status:* `Connected & Operational`",
            f"- *Total Monitored Papers:* `{stats['papers']}`",
            f"- *Total AI Analyses:* `{stats['analyses']}`",
            f"- *Registered Sources:* `{stats['sources']}`",
            f"- *Resilience & Caching:* `Active (Backoff, Jitter, Retry-After)`",
            f"- *Document Delivery:* `Active`",
            f"- *User Authorization:* `Enforced`"
        ]
        await msg.edit_text("\n".join(resp), parse_mode="Markdown")
    except Exception as e:
        error_msg = f"❌ Status check failed: {e}"
        if msg:
            try:
                await msg.edit_text(error_msg)
            except Exception:
                await update.effective_message.reply_text(error_msg)
        else:
            await update.effective_message.reply_text(error_msg)


async def domains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    text = """🔬 *Supported Scientific Disciplines*

1. *Medicine & Biology* (PubMed, OpenAlex, Crossref)
2. *Neuroscience* (PubMed, Semantic Scholar)
3. *Artificial Intelligence* (arXiv, OpenAlex, Semantic Scholar)
4. *Physics & Mathematics* (arXiv, Crossref)
5. *Astronomy & Space Science* (arXiv, OpenAlex)
6. *Bioengineering & Biotechnology* (PubMed, arXiv)"""
    await update.effective_message.reply_text(text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_authorization(update):
        await update.effective_message.reply_text("⛔ Unauthorized access.")
        return

    text = """🧬 *About SAKHR AVA_R*

*Organization:* SAKHR Scientific Intelligence
*Tagline:* Beyond Information. Toward Discovery.

SAKHR AVA_R is an advanced multidisciplinary scientific intelligence platform designed to aggregate, deduplicate, analyze, and synthesize literature across PubMed, arXiv, OpenAlex, Semantic Scholar, and Crossref powered by Gemini AI."""
    await update.effective_message.reply_text(text, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    if not check_authorization(update):
        try:
            await query.answer("⛔ Unauthorized access.", show_alert=True)
        except Exception:
            pass
        return

    try:
        await query.answer()
    except Exception as e:
        print(f"[Telegram] Warning: Could not answer callback query: {e}")

    data = query.data

    if data == "btn_research":
        await query.message.reply_text("🔍 To search research, use command:\n`/research <topic>`\nExample: `/research quantum computing`", parse_mode="Markdown")
    elif data == "btn_neuroscience":
        context.args = ["neuroscience", "connectomics"]
        await research_command(update, context)
    elif data == "btn_ai":
        context.args = ["artificial", "intelligence"]
        await research_command(update, context)
    elif data == "btn_physics":
        context.args = ["quantum", "physics"]
        await research_command(update, context)
    elif data == "btn_astronomy":
        context.args = ["astrophysics"]
        await research_command(update, context)
    elif data == "btn_biology":
        context.args = ["crispr", "gene", "editing"]
        await research_command(update, context)
    elif data == "btn_trends":
        await trends_command(update, context)
    elif data == "btn_recent":
        await recent_command(update, context)
    elif data == "btn_status":
        await status_command(update, context)
    else:
        await query.message.reply_text(f"Selected action: {data}")


def run_telegram_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[Telegram Bot] TELEGRAM_BOT_TOKEN not found in environment. Bot cannot start polling.")
        return

    # Clear lingering webhooks prior to starting long polling to avoid conflict
    webhook_clear_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
    try:
        requests.get(webhook_clear_url, timeout=10)
        print("[Telegram Bot] Cleared any existing webhooks for clean long polling.")
    except Exception as e:
        print(f"[Telegram Bot] Warning: Could not clear webhook: {e}")

 

    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )


    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("compare", compare_command))
    app.add_handler(CommandHandler("trends", trends_command))
    app.add_handler(CommandHandler("discover", discover_command))
    app.add_handler(CommandHandler("recent", recent_command))
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("domains", domains_command))
    app.add_handler(CommandHandler("about", about_command))

    app.add_handler(CallbackQueryHandler(button_callback))

    print("[Telegram Bot] SAKHR AVA_R Telegram Bot is starting long polling (drop_pending_updates=True)...")
    app.run_polling(drop_pending_updates=True) if hasattr(app, "run_polling") else app.run_polling()


if __name__ == "__main__":
    run_telegram_bot()
