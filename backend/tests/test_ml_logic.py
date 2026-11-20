from app.ml.class_map import classify_label, ppe_support
from app.ml.detector import Detection
from app.ml.ppe_classifier import associate
from app.ml.rule_engine import RuleSpec, evaluate, summarize
from app.ml.tracker import Tracker
from app.models.enums import PpeItem, Severity

H, V, G, S, M = PpeItem.HELMET, PpeItem.VEST, PpeItem.GLOVES, PpeItem.SAFETY_SHOES, PpeItem.MASK
FULL = {H: "positive", V: "positive", G: "positive", S: "positive", M: "positive"}


def person(x1=100, y1=100, x2=200, y2=400, conf=0.9):
    return Detection("person", None, (x1, y1, x2, y2), conf, "person")


def ppe(kind, item, box, conf=0.8):
    return Detection(kind, item, box, conf, item.value)


def run(dets, rules, support=FULL):
    return [evaluate(pp, i + 1, rules, support) for i, pp in enumerate(associate(dets))]


def test_class_names_from_common_datasets():
    assert classify_label("person") == ("person", None)
    assert classify_label("Hardhat") == ("has", H)
    assert classify_label("NO-Hardhat") == ("missing", H)
    assert classify_label("Safety Vest") == ("has", V)
    assert classify_label("NO-Safety Vest") == ("missing", V)
    assert classify_label("safety_shoes") == ("has", S)
    assert classify_label("no_mask") == ("missing", M)
    assert classify_label("Safety Cone") is None and classify_label("car") is None


def test_support_modes():
    kinds = {0: ("person", None), 1: ("has", H), 2: ("missing", H), 3: ("missing", V)}
    assert ppe_support(kinds) == {H: "both", V: "negative"}


def test_helmet_above_head_is_compliant_and_missing_is_violation():
    rules = [RuleSpec(H, True, Severity.HIGH)]
    ok = run([person(), ppe("has", H, (120, 90, 180, 150))], rules)[0]
    assert ok.state == "SAFE" and ok.items[H] is True and ok.compliance_score == 100.0
    bad = run([person()], rules)[0]
    assert bad.state == "VIOLATION" and bad.violations == [H] and bad.severity == Severity.HIGH


def test_zone_matters_a_helmet_at_the_feet_does_not_count():
    r = run([person(), ppe("has", H, (120, 350, 180, 390))], [RuleSpec(H, True)])[0]
    assert r.state == "VIOLATION"


def test_ppe_goes_to_the_right_person():
    a, b = person(100, 100, 200, 400), person(400, 100, 500, 400)
    helmet_on_b = ppe("has", H, (420, 90, 480, 150))
    ra, rb = run([a, b, helmet_on_b], [RuleSpec(H, True)])
    assert ra.state == "VIOLATION" and rb.state == "SAFE"


def test_partial_compliance_score_and_multiple_violations():
    rules = [RuleSpec(H, True, Severity.HIGH), RuleSpec(V, True, Severity.MEDIUM), RuleSpec(G, True, Severity.LOW)]
    r = run([person(), ppe("has", H, (120, 90, 180, 150))], rules)[0]
    assert r.violations == [V, G] and r.compliance_score == 33.3 and r.severity == Severity.MEDIUM


def test_explicit_negative_detection_flags_violation_and_negative_only_models_do_not_guess():
    rules = [RuleSpec(H, True)]
    negative_only = {H: "negative"}
    assert run([person()], rules, negative_only)[0].state == "SAFE"
    flagged = run([person(), ppe("missing", H, (120, 90, 180, 150))], rules, negative_only)[0]
    assert flagged.state == "VIOLATION"


def test_unsupported_items_are_not_checked_not_faked():
    r = run([person()], [RuleSpec(H, True), RuleSpec(V, True)], support={})[0]
    assert r.state == "WARNING" and r.violations == [] and r.compliance_score is None
    assert set(r.unchecked) == {H, V}


def test_optional_items_never_cause_violations():
    r = run([person(), ppe("has", H, (120, 90, 180, 150))], [RuleSpec(H, True), RuleSpec(M, False)])[0]
    assert r.state == "SAFE" and r.items[M] is False


def test_summary_counts():
    results = run([person(100, 100, 200, 400), person(400, 100, 500, 400), ppe("has", H, (420, 90, 480, 150))], [RuleSpec(H, True)])
    s = summarize(results)
    assert (s["workers"], s["compliant"], s["violations"], s["safety_score"]) == (2, 1, 1, 50.0)


def test_tracker_keeps_ids_stable_and_creates_new_ones():
    t = Tracker()
    assert t.update([(100, 100, 200, 400), (400, 100, 500, 400)]) == [1, 2]
    assert t.update([(405, 102, 505, 402), (104, 100, 204, 400)]) == [2, 1]
    assert t.update([(100, 100, 200, 400), (700, 100, 800, 400)])[1] == 3


def test_model_with_both_class_types_never_guesses_a_violation():
    both = {H: "both"}
    rules = [RuleSpec(H, True)]
    unseen = run([person()], rules, both)[0]
    assert unseen.items[H] is None and unseen.violations == [] and unseen.state == "WARNING"
    assert run([person(), ppe("has", H, (120, 90, 180, 150))], rules, both)[0].state == "SAFE"
    assert run([person(), ppe("missing", H, (120, 90, 180, 150))], rules, both)[0].state == "VIOLATION"


REAL_CLASSES = ["Hardhat", "Mask", "NO-Hardhat", "NO-Mask", "NO-Safety Vest", "Person", "Safety Cone", "Safety Vest", "machinery", "vehicle"]


def test_class_mapping_for_the_roboflow_construction_site_safety_model():
    kinds = {i: classify_label(n) for i, n in enumerate(REAL_CLASSES)}
    assert kinds[5] == ("person", None)
    assert kinds[0] == ("has", H) and kinds[2] == ("missing", H)
    assert kinds[7] == ("has", V) and kinds[4] == ("missing", V)
    assert kinds[1] == ("has", M) and kinds[3] == ("missing", M)
    assert kinds[6] is None and kinds[8] is None and kinds[9] is None  # cone, machinery, vehicle ignored
    support = ppe_support({i: k for i, k in kinds.items() if k})
    assert support == {H: "both", V: "both", M: "both"}  # gloves and shoes: not supported -> "not checked"
