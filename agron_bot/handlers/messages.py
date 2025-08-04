# messages.py – centralized bot responses (EN)

START_MESSAGE = (
    "🤖 *Welcome to Agron Bot!*\n"
    "Easily search the Agron database by providing a valid ID number.\n\n"
    "📌 *Available Commands:*\n"
    "/start – Show this help message\n"
    "/status – View your position in the queue\n"
    "/cancel – Cancel your current request (even if processing)\n"
    "/history – View your 5 most recent searches\n"
    "/stats – View your personal usage statistics\n\n"
    "✅ Simply send a valid 8–9 digit ID number to begin."
)

NO_QUEUE_MESSAGE = "✅ You currently have no active requests in the queue."

# Note: 'position_line' should be dynamically injected into this template
QUEUE_STATUS_MESSAGE = (
    "📊 There are currently {total} users in the queue.\n"
    "{position_line}\n"
    "⏳ Estimated wait time: ~{wait}."
)

CANCELLED_FROM_QUEUE_MESSAGE = "🗑️ Your request has been canceled and removed from the queue."
CANCEL_MARKED_MESSAGE = "📛 Your request has been marked for cancellation. It will be stopped if it's currently processing."

NO_HISTORY_MESSAGE = "📭 No completed searches found for your account."
HISTORY_HEADER = "📜 *Your last 5 completed searches:*"
HISTORY_LINE = "• ID {id_number} – ⏱️ {duration:.1f}s · 📅 {timestamp}"

NO_STATS_MESSAGE = "📭 No statistics found for your account."
STATS_TEMPLATE = (
    "📊 *Your Stats:*\n"
    "• Total Runs: *{total}*\n"
    "• Avg. Runtime: *{avg}* sec\n"
    "• Cancellations: *{cancelled}*"
)

NOT_FOUND_MESSAGE = "❗ No matching record was found for the given ID. Please double-check and try again."
