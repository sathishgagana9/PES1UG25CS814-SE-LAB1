
"""Metro fare calculator and transit card management."""

import hashlib
import shlex
from decimal import Decimal, InvalidOperation
from pathlib import PurePosixPath

import paramiko
from defusedxml import sax as safe_sax

# Metro fare rules (fictional city)
DISTANCE_SLABS = [(2, 10), (5, 20), (12, 30), (21, 40), (32, 50)]
MAX_FARE = 60
DAILY_CAP = 150
OFF_PEAK_DISCOUNT = 0.10
CONCESSIONS = {"student": 0.25, "senior": 0.50}
cards = {}


def base_of(km):
    """Return the base fare for a journey of the given distance."""
    return fare_for_distance(km)


def fare_for_distance(km):
    """Calculate the base fare from the journey distance."""
    for limit, fare in DISTANCE_SLABS:
        if km < limit:
            return fare
    return MAX_FARE


def is_peak(time_hhmm):
    """Return whether the given time falls within peak hours."""
    hour = int(time_hhmm.split(":")[0])
    return (8 <= hour <= 10) or (17 <= hour <= 20)


def journey_fare(km, time_hhmm, categories=None):
    """Calculate a journey fare after discounts and concessions."""
    if categories is None:
        categories = []

    fare = base_of(km)
    if not is_peak(time_hhmm):
        fare *= 1 - OFF_PEAK_DISCOUNT

    for category in categories:
        if category not in CONCESSIONS:
            raise ValueError(f"Unknown concession category: {category}")
        fare *= 1 - CONCESSIONS[category]

    return round(fare, 2)


def daily_total(journeys):
    """Calculate daily fares with the daily cap applied to the total."""
    fares = (
        journey_fare(km, time_hhmm, categories)
        for km, time_hhmm, categories in journeys
    )
    return min(sum(fares), DAILY_CAP)


def issue_card(card_id, balance=0):
    """Create a transit card with a non-negative balance."""
    amount = Decimal(str(balance))
    if not amount.is_finite() or amount < 0:
        raise ValueError("Initial balance must be non-negative and finite")

    cards[card_id] = {"balance": amount, "trips": []}


def tap_out(card_id, km, time_hhmm, categories=None):
    """Charge a card for a journey and record the trip."""
    if card_id not in cards:
        raise ValueError(f"Unknown card: {card_id}")

    fare = Decimal(str(journey_fare(km, time_hhmm, categories)))
    balance = cards[card_id]["balance"]

    if balance < fare:
        raise ValueError("Insufficient card balance")

    cards[card_id]["balance"] = balance - fare
    cards[card_id]["trips"].append(
        {"distance": km, "time": time_hhmm, "fare": fare}
    )
    return cards[card_id]["balance"]


def top_up(card_id, amount):
    """Add a positive amount to a transit card."""
    if card_id not in cards:
        raise ValueError(f"Unknown card: {card_id}")

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Top-up amount must be numeric") from exc

    if not amount.is_finite() or amount <= 0:
        raise ValueError("Top-up amount must be positive and finite")

    cards[card_id]["balance"] += amount
    return cards[card_id]["balance"]


def cheapest_route(routes):
    """Return the route with the lowest base fare."""
    if not routes:
        raise ValueError("At least one route is required")
    return min(routes, key=base_of)


def ticket_checksum(ticket_text):
    """Return a SHA-256 checksum for ticket text."""
    return hashlib.sha256(ticket_text.encode("utf-8")).hexdigest()


class StopHandler:
    """Collect stop names from safely parsed XML."""

    # SAX requires callback names in camelCase.
    # pylint: disable=invalid-name

    def __init__(self):
        self.stops = []

    def setDocumentLocator(self, locator):
        """Accept the document locator."""

    def startDocument(self):
        """Handle the beginning of the document."""

    def endDocument(self):
        """Handle the end of the document."""

    def startElement(self, name, attrs):
        """Record the name of each stop element."""
        if name == "stop":
            if "name" not in attrs:
                raise ValueError("Stop element is missing its name")
            self.stops.append(attrs["name"])

    def endElement(self, name):
        """Handle the end of an XML element."""

    def characters(self, content):
        """Ignore text content between elements."""

    def ignorableWhitespace(self, whitespace):
        """Ignore whitespace between elements."""

    def processingInstruction(self, target, data):
        """Ignore processing instructions."""

    def skippedEntity(self, name):
        """Handle skipped entities."""


def load_stops(xml_text):
    """Parse XML safely and return the stop names."""
    handler = StopHandler()
    safe_sax.parseString(xml_text.encode("utf-8"), handler)
    return handler.stops


def push_fares_to_gate(gate_host, fare_file):
    """Send a fare-install command to a verified SSH gate server."""
    remote_path = PurePosixPath(fare_file)

    if (
        not remote_path.is_absolute()
        or ".." in remote_path.parts
        or "\n" in fare_file
        or "\r" in fare_file
    ):
        raise ValueError("Fare file must be an absolute safe remote path")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        client.connect(gate_host, username="depot")
        command = "install_fares " + shlex.quote(str(remote_path))

        # B601: path validation and shell quoting are applied.
        # Review remote command safety before using this in production.
        _stdin, stdout, stderr = client.exec_command(command)  # nosec B601

        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gate installation failed: {error}")
    finally:
        client.close()


def main():
    """Run sample fare-calculator demonstrations."""
    print("Fare for exactly 2 km:", fare_for_distance(2))
    print("Fare for exactly 32 km:", fare_for_distance(32))
    print("Is 20:45 peak?", is_peak("20:45"))
    print(
        "Student + senior card, 10 km off-peak:",
        journey_fare(10, "14:00", ["student", "senior"]),
    )

    day = [
        (30, "08:15", []),
        (30, "18:30", []),
        (40, "21:00", []),
        (35, "22:30", []),
    ]
    print("Daily total (cap 150):", daily_total(day))

    issue_card("C1", 25)
    try:
        balance = tap_out("C1", 30, "09:00")
        print("Balance after a 30 km trip with Rs.25:", balance)
    except ValueError as exc:
        print("Trip declined:", exc)

    issue_card("C2", 0)
    print("Top up 0.1:", top_up("C2", 0.1))
    print("Top up another 0.2:", top_up("C2", 0.2))

    print(
        "Cheapest of routes 12 km / 5 km / 21 km:",
        cheapest_route([12, 5, 21]),
    )
    print("Ticket checksum:", ticket_checksum("C1|30km|09:00"))
    print(
        "Stops:",
        load_stops(
            "<line><stop name='Central'/>"
            "<stop name='Market'/></line>"
        ),
    )


if __name__ == "__main__":
    main()
