# Campaign rules — instructor reference

The current engine is `eco/campaign.py`, save schema `campaign-2.0`, rules `campaign-3.0`. This reference contains private economics and future events: keep it off the projected player screen. The player interface explains available decisions without showing a solution or an optimal allocation.

## Money and commitments

Each company starts with **20 credits once**. Balances never reset. Basic setup and chosen additions are paid when the first unanimous agreement takes effect.

| Company | Basic setup | Cost per committed operating quarter | Base outside income per available quarter |
| --- | ---: | ---: | ---: |
| MOBI | 3 | 1 | 0 |
| AUTO | 5 | 2 | 3 |
| BRAIN | 4 | 2 | 4 |
| GRID | 4 | 1 | 2 |
| FLEET | 5 | 2 | 4 |

Operating costs remain payable when tests or integration delays prevent revenue. Outside income is paid only when that capacity is outside committed operations. A company cannot use the same capacity twice. Insufficient operating funds stop service rather than silently creating negative cash; initial spending remains sunk.

Setup choices:

- MOBI: basic service, or enhanced support for 2 credits, adding 2 credits to full-capacity quarterly fleet revenue.
- AUTO: dedicated vehicles, or reconfigurable vehicles for 2 credits, reducing later intervention quotes by 1 credit and increasing available outside income after installation by 1 credit per quarter.
- BRAIN: a non-exclusive licence, or exclusivity until December at no extra setup cost. Exclusivity adds 2 credits to full-capacity quarterly revenue and prevents accepting a competing activity.
- GRID: basic capacity, or reserve capacity for 2 credits, reducing infrastructure intervention/expansion costs by 2 credits and helping reduce expansion overload risk.
- FLEET: standard preparation, or enhanced testing/continuity for 2 credits, reducing launch and expansion risk and intervention costs by 2 credits.

Added fleet revenue is distributed under the contract. The investing company receives its contractual share. An absent or replaced company's preparation does not transfer to a substitute. The company's earlier spending is preserved, and its capability can contribute again upon an agreed return.

## Contracts and calendar

Each quarter, MOBI proposes revenue amounts and investments in credits (to the nearest hundredth). Allocated revenue must equal the collective revenue at full capacity; contributions must match the investment quote exactly. A fresh unanimous agreement is required every quarter. Without agreement, revenue, operating charges and outside income for the quarter are zero; no previous contract is carried forward. Paid investments remain in place. Incidents can reduce receipts and agreed payouts by the same factor.

| Choice | Revenue at full capacity | Collective setup cost |
| --- | ---: | ---: |
| Custom integrated interfaces | 40 per quarter | 0 |
| Shared/documented interfaces | 38 per quarter | 6 |
| Open after approval | Full capacity in the first operating quarter, subject to tests | 0 |
| Phased pilot | 75% of full-capacity revenue in the first operating quarter, subject to tests | 3 |

MOBI/BRAIN commitments and expansion can modify full-capacity revenue. MOBI must allocate the updated total in credits. Incidents reduce actual receipts and agreed payouts by the same factor; operating costs remain payable after an agreement.

The instructor closes each quarter for all territories; the timer is independent. Each quarter settles once. An unsigned proposal expires. Earlier contracts remain in the history, but cannot substitute for a fresh agreement. Missed transport quarters cannot be recovered.

Automated vacant seats use basic setup profiles and accept proposals whose projected net income over the remaining quarters covers their outside activity. They do not count service revenue while an interface investment leaves a service suspended. Their thresholds are not displayed to players.

## Tests and local events

Commissioning is drawn once, in the first actually operated quarter:

| Launch | Standard FLEET | Prepared FLEET |
| --- | ---: | ---: |
| Open after approval | 45% interruption | 25% |
| Phased pilot | 5% | 3% |

An interruption removes that quarter's revenue while assets and operating costs remain. Expansion adds 10 credits at full capacity. Its first revenue-bearing quarter has a 35% overload risk, reduced to 8% with active GRID reserve or FLEET preparation. Overload halves that quarter's revenue; funded capacity remains installed.

Local draws occur in April, July and October:

| Family | Base weight | Effect |
| --- | ---: | --- |
| Ordinary activity | 15% | A fresh agreement in credits is required. |
| Additional demand | 15% | Expansion opportunity. |
| BRAIN outside offer | 15% | Private mobility opportunity. |
| Private cost increase | 20% | AUTO, GRID or FLEET incurs 2, 3 or 4 extra credits per committed quarter until December. |
| Public contribution reduction | 15% | Full-capacity fleet revenue falls by 6, 10 or 14 credits per quarter until December. |
| Infrastructure unavailable | 10% | Service stops until intervention or replacement. |
| Certification requirement | 10% | Adaptation is required to resume service. |

These are base weights. Incompatible events are excluded and remaining weights normalised. An operating fleet cannot receive two consecutive quiet periods. An already completed expansion, existing revenue reduction, incompatible mobility offer or previously applied private increase cannot be drawn again as a meaningless event. An unformed/suspended/unresolved territory keeps its existing situation.

The seed, territory, economic date and channel determine each draw. Independent target and intensity channels select eligible companies and three equally likely intensity levels. Actual candidates, exclusions, weights and draws are recorded. The game does not reroll until a preferred result appears.

A private cost shock is sent only to the affected company until year-end. It may request renegotiation or, where eligible, withdraw capacity. Withdrawal stops the fleet and requires a return or replacement agreement. A public revenue reduction requires the new agreement to distribute the reduced total in credits.

BRAIN's private outside offer pays **9 credits per quarter after departure** until December, when departure is accepted in the offered window. Exclusivity prevents departure. One position per territory can be covered by a substitute. A departed company retains its cash/history and can propose a return.

## Intervention and replacement

| Action | Integrated interfaces | Shared interfaces |
| --- | --- | --- |
| Repair/adapt | 7 credits; half the current quarter's revenue | 3 credits; service can resume this quarter |
| Replace unavailable/departed supplier | 9 credits; no transport revenue during integration this quarter | 3 credits; service can resume this quarter |
| Adopt shared interfaces later | 8 credits; earlier investment remains sunk | Already shared |

Active profile discounts apply, with a minimum intervention quote of 1 credit. The exact quote and delay are visible before consent. Pending commissioning/expansion tests can still apply. Late shared-interface investment does not clear a delay already committed earlier in that quarter.

The substitute requires at least 6 credits of revenue per quarter. The excluded company does not vote or pay for its own replacement. Its outside income continues. Returning requires a new agreement among all five companies and does not refund replacement costs. Suspending service does not repair an incident. Changing shares does not change paid profiles or interfaces for free. Standardising a suspended service does not restart it automatically.

## Accounts and debrief

Company result = final cash less the initial 20 credits, including outside activity.

Collective transport value = customer revenue less setup, profile, adaptation, operating and external-supplier costs. Distributed shares allocate revenue; they are not extra collective costs. Outside income is excluded from transport value.

The engine uses integer hundredths of a credit. Deterministic rounding assigns any remainder to the first contract share. Raw ZIP amounts use these hundredths; chart CSVs use credits. Every recorded transaction can be reconciled with balances.

Compare decisions with the circumstances actually received. The 320-campaign regression simulation covers four setup policies under 80 common seeds; it does not establish universal balance or replace a classroom pilot. No new event is invented for an old save or a missing historical decision.

Each player can publish requested revenue, a maximum proposed collective investment and their reasons. A public discussion lets players address a partner, offer a concession and explain acceptance or refusal. These requests do not replace consent to the published agreement. Private information is disclosed only by its owner.
