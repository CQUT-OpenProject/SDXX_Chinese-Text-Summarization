from collections import Counter


def chars(text):
    return [c for c in text if not c.isspace()]


def f1(overlap, predicted, reference):
    if not overlap or not predicted or not reference:
        return 0.0
    precision, recall = overlap / predicted, overlap / reference
    return 2 * precision * recall / (precision + recall)


def rouge_pair(prediction, reference):
    p, r = chars(prediction), chars(reference)
    scores = {}
    for n in (1, 2):
        pn = Counter(tuple(p[i:i+n]) for i in range(max(0, len(p)-n+1)))
        rn = Counter(tuple(r[i:i+n]) for i in range(max(0, len(r)-n+1)))
        scores[f"rouge{n}"] = f1(sum((pn & rn).values()), sum(pn.values()), sum(rn.values()))
    previous = [0] * (len(r) + 1)
    for pc in p:
        current = [0]
        for j, rc in enumerate(r, 1):
            current.append(previous[j-1] + 1 if pc == rc else max(previous[j], current[-1]))
        previous = current
    scores["rougeL"] = f1(previous[-1], len(p), len(r))
    return scores


def aggregate(predictions, references):
    if len(predictions) != len(references) or not predictions:
        raise ValueError("预测和参考摘要必须数量相同且非空")
    pairs = [rouge_pair(p, r) for p, r in zip(predictions, references)]
    return {key: sum(item[key] for item in pairs) / len(pairs) for key in pairs[0]}
