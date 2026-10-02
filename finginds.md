# Findings

| Leak | Where the data crossed | Where I closed it | What it still misses |
|---|---|---|---|
| OUT | `book_pickup` sends a booking to the transport service. The booking starts with the whole ticket (name, email, VIN, notes, etc). | `for_partner` in controls.py. Only 6 fields are allowed through, and the guardrail checks the two text fields the model writes. | The address and phone still go out because the driver needs them. The guardrail could miss an email written like "alex at example dot com". The model itself still sees everything the customer typed. |
| IN | `get_service_ticket` returns `intake_notes`, which has a license number and a card number in it. | *(not closed)* | The model can see both numbers. The prompt tells it not to repeat them but nothing actually stops it. |
| STORED | The audit log. main.py logs each turn and `book_pickup` logs what it sent. | `for_storage`, which runs inside `write_event` before anything is written. I also removed the template's log lines that printed the raw prompt. | Comprehend can miss things like lowercase names. The conversation history in memory and the traces aren't redacted. |

## Closing the IN Leak
I'd have to run every tool result through Comprehend before the model sees it. That means slower responses and more AWS calls. It could also remove things the model actually needs, like the bike model or dates. The better fix would be stopping staff from typing card and license numbers into the notes field in the first place.

## Fail Open or Fail Closed?
Both fail closed. If the guardrail is down, the pickup isn't sent and the customer is told staff will follow up. If Comprehend is down, the log entry only keeps the timestamp and ids and drops the rest. I chose this because a missed pickup can be fixed later but leaked data can't. The downside is the log gets less useful during an outage.

## With another day
I'd add tests that call the real Comprehend and guardrail instead of fakes, and look at redacting the traces and conversation history too.