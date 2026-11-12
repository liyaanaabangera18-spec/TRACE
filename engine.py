"""Transparent teaching rules; no trained model or probability of fraud."""
import random
from collections import Counter

DEFAULTS = {
    'harbour': dict(name='Harbour Bakes', night=72, round=64, repeat=14, orders=15,
                    complaint=True, route=True, shared_links=True, online=16,
                    settlement=12, reply='vague'),
    'petal': dict(name='Petal & Crumb', night=8, round=6, repeat=71, orders=92,
                  complaint=False, route=False, shared_links=False, online=78,
                  settlement=98, reply='invoice'),
}
CHECKS = {
    'payments': 10,
    'orders': 20,
    'complaint': 15,
    'route': 15,
    'links': 15,
    'digital': 10,
    'settlement': 15,
    'merchant': 10,
}
BUDGET = 60
FULFILLMENT_SUPPORT_THRESHOLD = 80
REPLIES = {'invoice', 'vague', 'no_reply'}
OTHER_SETTLEMENT_ACCOUNTS = ('ACCT-REC-02', 'ACCT-REC-03', 'ACCT-REC-04')
RESPONSES = [
    dict(id='monitor', label='Monitor quietly', min_checks=0,
         summary='Keep trading and set a review trigger for new evidence.'),
    dict(id='ask', label='Ask the merchant', min_checks=0,
         summary='Send one focused question about the changed payment pattern.'),
    dict(id='verify', label='Verify operations', min_checks=1,
         summary='Check order references and business details independently.'),
    dict(id='limit', label='Limit the suspicious flow', min_checks=2,
         summary='Consider a targeted, reversible restriction after human review.'),
    dict(id='analyst', label='Send to analyst review', min_checks=3,
         summary='Preserve the evidence pack for an authorised human decision.'),
]
SOURCE_DETAILS = {
    'payments': dict(
        name='Synthetic payment processor ledger',
        records='Transaction reference, timestamp, amount, payer reference and merchant ID.',
        use='Find after-hours activity, amount clustering, first-time payer share and co-occurring transaction patterns.',
        limit='Shows payment behavior, not customer intent, order fulfilment or criminality.',
    ),
    'orders': dict(
        name='Simulated bakery order and fulfilment register',
        records='Order references matched to payment references and fulfilment status.',
        use='Test whether transactions correspond to real bakery orders delivered to customers.',
        limit='A mismatch can reflect a missing reference or register error; it is not proof by itself.',
    ),
    'complaint': dict(
        name='Simulated customer complaint register',
        records='Complaint case and the payment reference supplied by the complainant.',
        use='Link a specific allegation to a transaction for targeted follow-up.',
        limit='An allegation and reference are leads; independently verify the activity.',
    ),
    'route': dict(
        name='Authorised simulated checkout test log',
        records='Controlled test-purchase result and the merchant identifier observed at checkout.',
        use='Establish whether the tested prohibited checkout is connected to this merchant.',
        limit='Direct evidence applies to the tested route and case; do not assume every order is prohibited.',
    ),
    'links': dict(
        name='Synthetic device and account-link register',
        records='Shared device or settlement identifiers across merchant profiles.',
        use='Identify relationships that warrant checking ownership and control.',
        limit='Shared infrastructure can be legitimate; a link does not establish common intent.',
    ),
    'digital': dict(
        name='Simulated public storefront snapshot',
        records='Recent menu, product and ordering activity visible on public web or social pages.',
        use='Check whether a visible operating business supports the merchant explanation.',
        limit='A storefront does not verify individual transactions; sparse web activity is not proof of wrongdoing.',
    ),
    'settlement': dict(
        name='Synthetic settlement ledger',
        records='Declared payout account and synthetic destination account reference recorded per transaction.',
        use='Trace payout shares by destination account reference and identify mismatches.',
        limit='No onward bank-transfer visibility is assumed; other destinations can have legitimate explanations.',
    ),
    'merchant': dict(
        name='Simulated merchant-response record',
        records='The merchant reply and any order references supplied in response to a focused question.',
        use='Generate leads that can be checked against independent order and fulfilment records.',
        limit='A reply is not independent proof; no reply is not evidence of prohibited activity.',
    ),
}


def simulate(payload):
    if not isinstance(payload, dict):
        raise ValueError('Review request must be an object')
    key = payload.get('merchant', 'petal')
    if key not in DEFAULTS:
        raise ValueError('Unknown merchant')
    base = DEFAULTS[key]
    raw = payload.get('inputs', {})
    if not isinstance(raw, dict):
        raise ValueError('Inputs must be an object')

    values = {}
    for field in ('night', 'round', 'repeat', 'orders', 'online', 'settlement'):
        value = float(raw.get(field, base[field]))
        if not 0 <= value <= 100:
            raise ValueError('Percentages must be between 0 and 100')
        values[field] = value
    for field in ('complaint', 'route', 'shared_links'):
        values[field] = raw.get(field, base[field])
        if not isinstance(values[field], bool):
            raise ValueError('Evidence switches must be true or false')
    values['reply'] = raw.get('reply', base['reply'])
    if values['reply'] not in REPLIES:
        raise ValueError('Unknown merchant response')

    requested_checks = payload.get('checks', [])
    if not isinstance(requested_checks, (list, tuple)) or any(
        not isinstance(check, str) for check in requested_checks
    ):
        raise ValueError('Checks must be a list of names')
    checks = list(dict.fromkeys(requested_checks))
    if any(check not in CHECKS for check in checks):
        raise ValueError('Unknown check')
    spent = sum(CHECKS[check] for check in checks)
    if spent > BUDGET:
        raise ValueError(f'The review budget is {BUDGET} minutes')

    # Keep each observed dimension independent so the generator does not invent correlations.
    rng = random.Random(417)
    settlement_rng = random.Random(9913)
    record_count = 1000
    index_sets = {
        field: set(rng.sample(range(record_count), round(values[field] * 10)))
        for field in ('night', 'round', 'repeat', 'orders', 'settlement')
    }
    records = []
    returning_count = len(index_sets['repeat'])
    returning_payer_count = max(1, min(40, returning_count // 8 or 1))
    for index in range(record_count):
        after_hours = index in index_sets['night']
        rounded_amount = index in index_sets['round']
        returning = index in index_sets['repeat']
        fulfilled = index in index_sets['orders']
        declared_account = index in index_sets['settlement']
        records.append(dict(
            id=f'TX-{index + 1:04}',
            hour=rng.randrange(22, 24) if after_hours else rng.randrange(7, 22),
            amount=rng.choice([500, 1000, 2000]) if rounded_amount else rng.choice([179, 195, 239, 349]),
            payer_ref=f'RETURN-{rng.randrange(returning_payer_count) + 1:03}' if returning else f'NEW-{index + 1:04}',
            returning=returning,
            order_ref=f'ORD-{index + 1:04}' if fulfilled else None,
            fulfilled_order=fulfilled,
            settlement_destination='ACCT-OWN-01' if declared_account else settlement_rng.choices(
                OTHER_SETTLEMENT_ACCOUNTS, weights=(5, 3, 2), k=1
            )[0],
            declared_account=declared_account,
        ))
    rng.shuffle(records)
    metrics = dict(
        night=sum(record['hour'] >= 22 for record in records) / 10,
        round=sum(record['amount'] in (500, 1000, 2000) for record in records) / 10,
        repeat=sum(record['returning'] for record in records) / 10,
        orders=sum(record['fulfilled_order'] for record in records) / 10,
        settlement=sum(record['declared_account'] for record in records) / 10,
    )
    destination_counts = Counter(record['settlement_destination'] for record in records)
    destination_order = ('ACCT-OWN-01',) + OTHER_SETTLEMENT_ACCOUNTS
    all_settlement_destinations = [
        dict(
            account_ref=account_ref,
            declared=account_ref == 'ACCT-OWN-01',
            count=destination_counts[account_ref],
            share=round(destination_counts[account_ref] / record_count * 100, 1),
        )
        for account_ref in destination_order
    ]
    settlement_destinations = all_settlement_destinations if 'settlement' in checks else None

    pattern_signals = []
    if 'payments' in checks:
        pattern_signals = [
            dict(label='After-hours payments', value=metrics['night'], threshold=20,
                 direction='above', triggered=metrics['night'] > 20,
                 alternative='Late delivery orders, a changed closing time or delayed batch posting.',
                 corroborate='Compare timestamps with verified order times and the merchant’s operating hours.'),
            dict(label='Round-amount payments', value=metrics['round'], threshold=40,
                 direction='above', triggered=metrics['round'] > 40,
                 alternative='Fixed-price catering, gift bundles or a promotion can create round totals.',
                 corroborate='Compare the amounts with itemised orders, promotion terms and refunds.'),
            dict(label='Transactions from returning payers', value=metrics['repeat'], threshold=30,
                 direction='below', triggered=metrics['repeat'] < 30,
                 alternative='A seasonal rush, new location or legitimate campaign can bring first-time buyers.',
                 corroborate='Check distinct payer references against order and fulfilment records.'),
        ]
    for record in records:
        record['pattern_flags'] = []
        if 'payments' in checks:
            if metrics['night'] > 20 and record['hour'] >= 22:
                record['pattern_flags'].append('after-hours')
            if metrics['round'] > 40 and record['amount'] in (500, 1000, 2000):
                record['pattern_flags'].append('round amount')
            if metrics['repeat'] < 30 and not record['returning']:
                record['pattern_flags'].append('first-time payer')
        if 'orders' in checks and metrics['orders'] < FULFILLMENT_SUPPORT_THRESHOLD and not record['fulfilled_order']:
            record['pattern_flags'].append('no order match')
        if 'settlement' in checks and metrics['settlement'] < 50 and not record['declared_account']:
            record['pattern_flags'].append('other settlement destination')
    priority_records = sorted(records, key=lambda record: (-len(record['pattern_flags']), record['id']))
    matched_transaction_ref = priority_records[0]['id']
    map_sample_records = []
    for account_ref in destination_order:
        destination_records = [
            record for record in priority_records
            if record['settlement_destination'] == account_ref
        ]
        map_sample_records.extend(destination_records[:3])
    sampled_ids = {record['id'] for record in map_sample_records}
    if len(map_sample_records) < 12:
        map_sample_records.extend(
            record for record in priority_records
            if record['id'] not in sampled_ids
        )
    map_sample_records = map_sample_records[:12]
    money_map = dict(
        synthetic=True,
        payments_checked='payments' in checks,
        settlement_checked='settlement' in checks,
        payer_mix=dict(
            first_time=round(100 - metrics['repeat'], 1),
            repeat=round(metrics['repeat'], 1),
        ),
        settlement_destinations=all_settlement_destinations,
        sample_transactions=[
            dict(
                id=record['id'],
                hour=record['hour'],
                amount=record['amount'],
                payer_ref=record['payer_ref'],
                settlement_destination=record['settlement_destination'],
            )
            for record in map_sample_records
        ],
    )

    hour_bands = [
        ('Opening · 07–10', lambda record: 7 <= record['hour'] < 11),
        ('Daytime · 11–16', lambda record: 11 <= record['hour'] < 17),
        ('Evening · 17–21', lambda record: 17 <= record['hour'] < 22),
        ('After hours · 22–23', lambda record: record['hour'] >= 22),
    ]
    returning_payers = Counter(record['payer_ref'] for record in records if record['returning'])
    transaction_patterns = None
    if 'payments' in checks:
        transaction_patterns = dict(
            total_transactions=record_count,
            time_bands=[dict(label=label, count=sum(test(record) for record in records)) for label, test in hour_bands],
            amount_mix=[
                dict(label='Round amounts', count=sum(record['amount'] in (500, 1000, 2000) for record in records)),
                dict(label='Other amounts', count=sum(record['amount'] not in (500, 1000, 2000) for record in records)),
            ],
            payer_mix=[
                dict(label='Returning-payer transactions', count=sum(record['returning'] for record in records)),
                dict(label='First-time-payer transactions', count=sum(not record['returning'] for record in records)),
            ],
            co_occurrence=[
                dict(label='After hours + round amount', count=sum(record['hour'] >= 22 and record['amount'] in (500, 1000, 2000) for record in records)),
                dict(label='After hours + first-time payer', count=sum(record['hour'] >= 22 and not record['returning'] for record in records)),
                dict(label='Round amount + first-time payer', count=sum(record['amount'] in (500, 1000, 2000) and not record['returning'] for record in records)),
            ],
            frequent_payers=[dict(payer=reference, transactions=count) for reference, count in returning_payers.most_common(5)],
        )

    reasons, gaps, evidence, concern_sources = [], [], [], []
    unusual = 0
    if 'payments' in checks:
        for condition, message in (
            (metrics['night'] > 20, 'Payments after closing exceed the demo threshold of 20%.'),
            (metrics['round'] > 40, 'Round amounts exceed the demo threshold of 40%.'),
            (metrics['repeat'] < 30, 'Returning payers are below the demo threshold of 30%.'),
        ):
            if condition:
                unusual += 1
                reasons.append(message)
        evidence.append(dict(check='payments',
            title='Payment ledger',
            text=f"{metrics['night']}% after 10 pm · {metrics['round']}% round amounts · {metrics['repeat']}% returning payers. Each pattern can have a legitimate explanation.",
        ))
        if unusual:
            concern_sources.append('payments')
    else:
        gaps.append('Payment pattern check not performed.')

    supported = 'orders' in checks and metrics['orders'] >= FULFILLMENT_SUPPORT_THRESHOLD
    if 'orders' in checks:
        evidence.append(dict(check='orders',
            title='Independent order verification',
            text=f"{metrics['orders']}% of payments link to fulfilled bakery orders in the simulated verification register. An invoice upload alone does not count.",
        ))
        if supported:
            reasons.append('Independent fulfilment records corroborate a legitimate operating explanation.')
        else:
            concern_sources.append('fulfillment')
            reasons.append(f'Independent fulfilment is below the illustrative {FULFILLMENT_SUPPORT_THRESHOLD}% support threshold; reconcile unmatched transactions before concluding why.')
    else:
        gaps.append('Fulfilled orders have not been independently checked.')

    complaint = 'complaint' in checks and values['complaint']
    direct = 'route' in checks and values['route']
    if direct:
        concern_sources.append('checkout')
    for check, title, yes, no in (
        ('complaint', 'Complaint verification',
         f'Simulated complaint CMP-017 names payment reference {matched_transaction_ref}. The allegation is a lead, not proof of the activity.',
         'No matching complaint was found in the simulated register. Absence of complaints is not clearance.'),
        ('route', 'Checkout verification',
         f'Authorised test TEST-017 connects this merchant to payment reference {matched_transaction_ref} through a simulated prohibited checkout. This is direct activity evidence in this scenario.',
         'The authorised test found no prohibited route. This does not rule out undiscovered routes.'),
    ):
        if check in checks:
            evidence.append(dict(check=check, title=title, text=yes if values[check] else no))
        else:
            gaps.append(title + ' not performed.')
    if complaint:
        concern_sources.append('complaint')

    if 'links' in checks:
        if values['shared_links']:
            text = 'A device or settlement identifier also appears on another merchant profile. Shared ownership can be legitimate; verify the relationship.'
            concern_sources.append('links')
        else:
            text = 'No shared device or settlement identifier was found in the reviewed sample.'
        evidence.append(dict(check='links', title='Device and account links', text=text))
    else:
        gaps.append('Device and account links have not been checked.')

    if 'digital' in checks:
        if values['online'] >= 60:
            text = 'Recent menu, product and ordering activity is visible online. This supports a real storefront but does not verify each payment.'
        elif values['online'] >= 25:
            text = 'Some online activity is visible, but it does not independently verify fulfilled orders.'
        else:
            text = 'Little recent menu or product activity was found. Sparse web presence is not proof of prohibited activity.'
        evidence.append(dict(check='digital', title='Website and social activity', text=text))
    else:
        gaps.append('Website and social activity have not been checked.')

    if 'settlement' in checks:
        other_percent = round(100 - metrics['settlement'], 1)
        evidence.append(dict(check='settlement',
            title='Settlement destination',
            text=f"{metrics['settlement']}% reaches the declared settlement account; {other_percent}% reaches other synthetic destination account references. Account references do not identify owners, and no onward-transfer visibility is assumed.",
        ))
        if metrics['settlement'] < 50:
            concern_sources.append('settlement')
    else:
        gaps.append('Settlement destinations have not been checked.')

    if 'merchant' in checks:
        reply_text = {
            'invoice': 'The merchant replied with itemised order details. Treat the response as a lead; independently verify fulfilment.',
            'vague': 'The merchant replied, but the explanation did not include enough order references to verify the change.',
            'no_reply': 'No response was received within 48 hours. Non-response is not evidence of prohibited activity.',
        }[values['reply']]
        evidence.append(dict(check='merchant', title='Merchant response', text=reply_text))
        if values['reply'] != 'invoice':
            concern_sources.append('merchant_response')
    else:
        gaps.append('Merchant explanation has not been requested.')
    merchant_response_needs_verification = 'merchant' in checks and 'orders' not in checks
    if merchant_response_needs_verification:
        reasons.append('The merchant response has not been matched to independent order and fulfilment records.')

    if direct:
        level = 4
        reasons.insert(0, 'Verified checkout evidence connects prohibited activity to this merchant.')
        if supported:
            reasons.append('Genuine fulfilled orders also exist: investigate mixed activity rather than assuming the whole business is fraudulent.')
        basis = 'Preserve the matched payment and checkout evidence for an authorised human review.'
    elif supported and 'payments' in checks and not complaint and not (set(concern_sources) - {'payments'}):
        level = 0
        reasons.insert(0, 'Corroborated fulfilment supports continued trading with monitoring, not unconditional clearance.')
        basis = 'Keep trading and reopen the review if new contradictory evidence appears.'
    elif len(set(concern_sources)) >= 2:
        level = 3
        reasons.insert(0, 'Concerns appear in more than one evidence source; consider a narrowly targeted, reversible response.')
        basis = 'Have a human reviewer identify the specific flow before any restriction.'
    elif concern_sources or merchant_response_needs_verification:
        level = 2
        if merchant_response_needs_verification and not concern_sources:
            reasons.insert(0, 'The merchant supplied an explanation, but it has not been independently verified.')
            basis = 'Match the merchant response to independent order and fulfilment records.'
        else:
            reasons.insert(0, 'The available evidence calls for targeted verification, not a finding of guilt.')
            basis = 'Resolve the strongest evidence gap before escalating the response.'
    else:
        level = 1
        reasons.insert(0, 'The evidence is incomplete; ask one focused question before deciding whether stronger checks are needed.')
        basis = 'Keep the case open while the merchant explains the change.'

    recommendation = RESPONSES[level]
    response_options = []
    for response in RESPONSES:
        direct_override = response['id'] == 'analyst' and direct
        enabled = len(checks) >= response['min_checks'] or direct_override
        response_options.append(dict(**response, enabled=enabled))

    legacy_action = 'monitor' if level == 0 else 'escalate' if level >= 3 else 'verify'
    legacy_labels = {
        'monitor': 'Continue trading with monitoring',
        'verify': 'Resolve the evidence gap',
        'escalate': 'Escalate for authorised review',
    }
    next_step = basis
    if direct:
        conclusion = 'Direct prohibited-checkout evidence is present in this synthetic case; preserve the exact transaction and test record for authorised human review.'
        actions = [
            f'Preserve {matched_transaction_ref} and the authorised test-purchase result.',
            'Check whether the same transaction also has an order, complaint or settlement reference.',
            'Send the evidence pack to an authorised human reviewer; do not label every order fraudulent.',
        ]
    elif level == 0:
        conclusion = 'Independent order matches support a legitimate explanation; continue monitoring and reopen if a contradictory source appears.'
        actions = [
            'Keep the merchant trading under proportionate monitoring.',
            'Record the verified fulfilment rate and payment-pattern baseline.',
            'Reopen only if new contradictory evidence appears.',
        ]
    elif len(set(concern_sources)) >= 2:
        conclusion = 'More than one independent evidence source raises a concern. Reconcile the same TX references across those sources before considering any restriction.'
        actions = [
            f'Preserve {matched_transaction_ref} and the overlapping pattern flags.',
            'Compare each reference with the relevant order, complaint, checkout or settlement register.',
            'Have a human reviewer scope any reversible action to the evidence-supported flow.',
        ]
    elif 'fulfillment' in concern_sources:
        conclusion = 'The independent fulfilment register does not match enough payment references to support the declared bakery activity. Reconcile missing references and register coverage; this mismatch alone does not prove prohibited activity.'
        actions = [
            'Preserve the unmatched TX references, amounts and timestamps.',
            'Reconcile them against point-of-sale orders, receipts and delivery records; check for missing or duplicated references.',
            'Verify a complaint or checkout link independently before considering any restriction.',
        ]
    elif complaint:
        conclusion = 'A complaint is linked to a payment reference, but the allegation is not independently established.'
        actions = [
            f'Preserve the complaint reference and linked payment {matched_transaction_ref}.',
            'Verify the alleged checkout or service activity and compare it with the merchant order record.',
            'Do not restrict the merchant based on the complaint alone.',
        ]
    elif 'settlement' in concern_sources:
        conclusion = 'The checked settlement ledger shows a mismatch with the declared destination. It does not establish who ultimately controlled the funds or why they moved.'
        actions = [
            f'Preserve {matched_transaction_ref} and the settlement destination recorded for it.',
            'Check account ownership and reconcile the destination with supplier, payroll or other documented business payments.',
            'Seek independent checkout or complaint evidence before considering a restriction.',
        ]
    elif 'links' in concern_sources:
        conclusion = 'A device or account identifier is shared across merchant profiles. This is a relationship lead, not proof that the businesses share prohibited activity.'
        actions = [
            f'Preserve {matched_transaction_ref} and the shared identifier.',
            'Verify ownership, authorised service-provider use and the relationship between the merchant profiles.',
            'Look for independent transaction or checkout evidence before escalating.',
        ]
    elif 'merchant_response' in concern_sources or merchant_response_needs_verification:
        if values['reply'] == 'no_reply':
            conclusion = 'No response was received within 48 hours. Silence is not evidence of wrongdoing; continue with independent records rather than repeating the same request.'
            actions = [
                'Do not interpret silence as proof or send repeated generic document requests.',
                'Compare payment references with independent order, fulfilment, complaint and checkout records.',
                'Escalate only if independently verified evidence supports a specific concern.',
            ]
        elif values['reply'] == 'vague':
            conclusion = 'The merchant replied, but the explanation does not resolve the transaction-level question.'
            actions = [
                'Ask one focused follow-up for missing order references; avoid repeating a generic request.',
                'Match supplied references against independent point-of-sale and fulfilment records.',
                'Use payment and checkout evidence, not response quality alone, to decide whether to escalate.',
            ]
        else:
            conclusion = 'The merchant supplied an explanation, but it remains a lead until independently matched to business records.'
            actions = [
                'Match the supplied order references against the independent fulfilment register.',
                'Check transaction time, amount and destination for contradictions.',
                'Escalate only if the independent records conflict with the explanation.',
            ]
    elif 'payments' in concern_sources:
        conclusion = 'The payment ledger contains unusual patterns, but payment behavior alone does not establish prohibited activity.'
        actions = [
            f'Preserve {matched_transaction_ref} and the overlapping payment-pattern flags.',
            'Check exact references against independent orders, fulfilment records and the merchant explanation.',
            'Verify a complaint or prohibited checkout before considering a restriction.',
        ]
    else:
        conclusion = 'No checked source has established a concern yet; unchecked sources remain unknown.'
        actions = [
            'Start with the payment ledger to identify transaction-level patterns.',
            'Select an independent order or fulfilment check to test the business explanation.',
            'Use a complaint or checkout test only when it answers a specific unresolved question.',
        ]
    triage_plan = dict(
        conclusion=conclusion,
        actions=actions,
        decision_rule='A payment anomaly is a lead. Stronger conclusions require independent corroboration; one missing register match or a complaint is not a fraud finding.',
    )
    for item in evidence:
        item.update(SOURCE_DETAILS[item['check']])
    source_register = [
        dict(check=check, **details, checked=check in checks)
        for check, details in SOURCE_DETAILS.items()
    ]
    follow_up_sources = sorted(set(concern_sources))
    if merchant_response_needs_verification and 'merchant_response_unverified' not in follow_up_sources:
        follow_up_sources.append('merchant_response_unverified')
    observed_values = {}
    for check, fields in (
        ('payments', ('night', 'round', 'repeat')),
        ('orders', ('orders',)),
        ('complaint', ('complaint',)),
        ('route', ('route',)),
        ('links', ('shared_links',)),
        ('digital', ('online',)),
        ('settlement', ('settlement',)),
        ('merchant', ('reply',)),
    ):
        if check in checks:
            observed_values.update({field: values[field] for field in fields})
    published_records = []
    if 'payments' in checks:
        for record in priority_records[:12]:
            published = {field: record[field] for field in (
                'id', 'hour', 'amount', 'payer_ref', 'returning', 'pattern_flags',
            )}
            if 'orders' in checks:
                published.update(order_ref=record['order_ref'], fulfilled_order=record['fulfilled_order'])
            if 'settlement' in checks:
                published.update(
                    settlement_destination=record['settlement_destination'],
                    declared_account=record['declared_account'],
                )
            published_records.append(published)
    return dict(
        merchant=base['name'], values=observed_values, checks=checks, spent=spent,
        remaining=BUDGET - spent, budget=BUDGET,
        metrics=metrics if 'payments' in checks else None,
        records=published_records,
        settlement_destinations=settlement_destinations,
        money_map=money_map,
        matched_transaction_ref=matched_transaction_ref,
        transaction_patterns=transaction_patterns,
        pattern_signals=pattern_signals,
        evidence=evidence, gaps=gaps, reasons=reasons, action=legacy_action,
        label=legacy_labels[legacy_action], next=next_step, unusual=unusual,
        recommendation=dict(level=level, id=recommendation['id'], label=recommendation['label'], basis=basis),
        responses=response_options,
        sources=source_register,
        triage_plan=triage_plan,
        follow_up_sources=follow_up_sources,
        risk_sources=sorted(set(concern_sources)),
        disclosure='Synthetic scenario. Rules and thresholds are illustrative, not validated detection performance or probabilities.',
    )
