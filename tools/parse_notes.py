"""Parse pasted '=== NOTE ===' blocks into Vault note JSON files.

Usage: python3 -I parse_notes.py <input.txt> <out_dir>
Writes one <doc_id>.json per note plus manifest.json [{doc_id, title}].
"""
import hashlib, json, os, re, sys

SECTIONS = ["무엇을 했나", "계기와 문제의식", "과정과 결과", "배우고 바뀐 점", "연결"]
FOLDERS = {"교과", "창체", "독서", "수상", "진로", "대입", "일상", "기타"}


def parse(text):
    notes = []
    for chunk in text.split("=== NOTE ===")[1:]:
        lines = chunk.strip("\n").split("\n")
        header = lines[0]
        body_lines = lines[1:]
        # header may be one line ("title: .. folder: .. date: ..") or several
        while body_lines and re.match(r"^\s*(title|folder|date)\s*:", body_lines[0]):
            header += " " + body_lines.pop(0)
        m = re.search(r"title:\s*(.*?)\s*(?=folder:|date:|$)", header)
        f = re.search(r"folder:\s*(\S+)", header)
        d = re.search(r"date:\s*(.*)$", header)
        title = m.group(1).strip()
        folder = f.group(1).strip() if f else "기타"
        if folder not in FOLDERS:
            folder = "기타"
        date_raw = d.group(1).strip() if d else ""
        date = re.match(r"[\d-]*", date_raw).group(0)
        date_note = "[확인 필요]" in date_raw

        sections, cur = {}, None
        for ln in body_lines:
            s = ln.strip()
            key = s.lstrip("#").strip()
            if key in SECTIONS:
                cur = key
                sections[cur] = []
                continue
            if s in ("---", "") and cur is None:
                continue
            if cur is None:
                cur = "무엇을 했나"
                sections[cur] = []
            if s.startswith("* "):
                s = "- " + s[2:]
            sections[cur].append(s)

        out = []
        for k in SECTIONS:
            content = [x for x in sections.get(k, []) if x and x != "*" and x != "-"]
            if content:
                out.append("## " + k)
                out.extend(content)
                out.append("")
        body = "\n".join(out).strip()
        if date_note:
            body = "- 날짜 [확인 필요]\n\n" + body
        doc_id = "n-" + hashlib.sha1(title.encode()).hexdigest()[:12]
        notes.append({"doc_id": doc_id, "title": title, "folder": folder, "date": date, "body": body})
    return notes


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    notes = parse(open(src, encoding="utf-8").read())
    manifest = []
    for n in notes:
        doc = {k: n[k] for k in ("title", "folder", "date", "body")}
        doc["updated"] = "2026-10-09T00:00:00Z"
        with open(os.path.join(out_dir, n["doc_id"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        manifest.append({"doc_id": n["doc_id"], "title": n["title"]})
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(len(notes), "notes")
    for n in manifest:
        print(n["doc_id"], n["title"])


if __name__ == "__main__":
    main()
