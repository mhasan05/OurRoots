from decimal import Decimal
from .models import BudgetCategoryRule, BudgetSessionBreakdown, BudgetSessionExperience


def compute_experiences_cost(session):
    """
    Uses selected experiences ranges:
    - take midpoint of each experience range * quantity
    """
    total = Decimal("0")
    for se in BudgetSessionExperience.objects.filter(session=session).select_related("experience"):
        exp = se.experience
        mid = (exp.min_cost + exp.max_cost) / 2
        total += (mid * se.quantity)
    return total


def generate_default_breakdown(session):
    """
    Use style-based default rules, plus computed experiences cost,
    and emergency buffer = 10% of subtotal by default.
    """
    rules = {r.category: r for r in BudgetCategoryRule.objects.filter(style=session.style)}
    flights = rules.get("flights").default_cost if rules.get("flights") else Decimal("0")
    accommodation = rules.get("accommodation").default_cost if rules.get("accommodation") else Decimal("0")
    transportation = rules.get("transportation").default_cost if rules.get("transportation") else Decimal("0")
    food = rules.get("food").default_cost if rules.get("food") else Decimal("0")

    experiences_cost = compute_experiences_cost(session)
    if rules.get("experiences"):
        # take max(default, computed) so user selections matter
        experiences = max(rules["experiences"].default_cost, experiences_cost)
    else:
        experiences = experiences_cost

    subtotal = flights + accommodation + transportation + food + experiences
    emergency = rules.get("emergency").default_cost if rules.get("emergency") else (subtotal * Decimal("0.10"))

    breakdown, _ = BudgetSessionBreakdown.objects.get_or_create(session=session)
    breakdown.flights = flights
    breakdown.accommodation = accommodation
    breakdown.transportation = transportation
    breakdown.food = food
    breakdown.experiences = experiences
    breakdown.emergency = emergency
    breakdown.save()

    session.total_estimate = breakdown.total()
    session.save(update_fields=["total_estimate"])

    return breakdown
