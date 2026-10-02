import json

from controls import PARTNER_FIELDS
from store import write_event
from tools import TICKETS, book_pickup

TICKET = TICKETS["RT-2207"]
CARD = "4111 1111 1111 1111"
LICENSE = "S12345678"

BOOKING_ARGS = {
    "ticket_id": "RT-2207",
    "pickup_window": "Sat 10am-1pm",
    "bike_notes": f"Rear tyre flat. Text or email {TICKET['email']} when the truck is close.",
}

TURN = {
    "event": "turn",
    "session_id": "test-session",
    "prompt": f"Hi, it's {TICKET['customer_name']}, ticket RT-2207. Reach me at {TICKET['email']} or {TICKET['phone']}.",
    "answer": "Your bike is waiting on parts and should be ready Thursday.",
}


def _records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_transport_payload_has_no_personal_data_beyond_address_and_phone(aws_fakes):
    book_pickup.invoke(BOOKING_ARGS)

    sent = (aws_fakes / "outbox.jsonl").read_text()
    for value in (
        TICKET["customer_name"],
        TICKET["email"],
        TICKET["bike"]["vin"],
        TICKET["bike"]["plate"],
        CARD,
        LICENSE,
    ):
        assert value not in sent

    payload = _records(aws_fakes / "outbox.jsonl")[-1]
    assert set(payload) <= set(PARTNER_FIELDS)
    assert payload["contact_phone"] == TICKET["phone"]
    assert payload["pickup_address"] == TICKET["pickup_address"]


def test_nothing_sent_when_guardrail_unavailable(aws_fakes, guardrail_down):
    result = book_pickup.invoke(BOOKING_ARGS)

    assert "not booked" in result
    assert not (aws_fakes / "outbox.jsonl").exists()


def test_audit_record_has_no_raw_personal_data(aws_fakes):
    write_event(TURN)

    stored = (aws_fakes / "audit.jsonl").read_text()
    for value in (TICKET["customer_name"], TICKET["email"], TICKET["phone"]):
        assert value not in stored
    assert "[EMAIL]" in stored


def test_pickup_audit_entry_redacts_address_and_phone(aws_fakes):
    book_pickup.invoke({**BOOKING_ARGS, "bike_notes": "Rear tyre flat."})

    stored = (aws_fakes / "audit.jsonl").read_text()
    assert TICKET["phone"] not in stored
    assert "12 Example Lane" not in stored


def test_storage_fails_closed_when_comprehend_unavailable(aws_fakes, comprehend_down):
    write_event(TURN)

    record = _records(aws_fakes / "audit.jsonl")[-1]
    assert TICKET["email"] not in json.dumps(record)
    assert record["redaction"] == "unavailable, content dropped"