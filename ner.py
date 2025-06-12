import spacy
import re
import os
from datetime import datetime, timezone

nlp = spacy.load("en_core_web_md")

def classify_entities(entities):
    education_keywords = ["university", "college", "institute", "bachelor", "master", "phd", "msc", "school", "academy"]
    skill_keywords = [
        # 🧠 М’які навички
        "communication", "teamwork", "leadership", "problem solving", "time management",
        "adaptability", "critical thinking", "creativity", "attention to detail", "organization",
        # 🖥 IT
        "python", "java", "c++", "sql", "html", "css", "javascript", "git", "linux", "docker",
        "data analysis", "machine learning", "deep learning", "tensorflow", "pandas", "numpy",
        "power bi", "excel", "tableau", "aws", "azure", "cloud", "api development",
        # 📊 Бізнес
        "microsoft office", "word", "powerpoint", "erp", "sap", "crm", "data entry",
        "project management", "budgeting", "salesforce", "accounting", "forecasting",
        # 🛠 Робітничі
        "welding", "carpentry", "plumbing", "electrical", "machinery operation", "maintenance",
        "blueprint reading", "forklift operation", "repair", "construction",
        # 🍽 Сфера обслуговування
        "customer service", "cash handling", "order taking", "food preparation", "cooking",
        "bartending", "dishwashing", "cleaning", "POS systems", "inventory",
        # 🚛 Транспорт
        "driving", "truck driving", "navigation", "route planning", "vehicle maintenance",
        "logistics", "delivery", "loading", "unloading", "warehouse management",
        # 🧑‍⚕️ Медицина
        "first aid", "patient care", "medication administration", "vital signs", "nursing",
        "record keeping", "elder care", "childcare", "rehabilitation", "sanitation",
        # 🎨 Креатив
        "photoshop", "illustrator", "graphic design", "video editing", "photography",
        "social media", "marketing", "branding", "content creation",
        # 📞 Адміністративні
        "filing", "scheduling", "call handling", "typing", "office management",
        "calendar management", "email management", "document preparation", "clerical duties"
    ]
    profession_keywords = ["C Developer", "Java Developer", "Data Scientist", "Project Manager", "UI/UX designer", "Graphic designer", "QA engineer", "HR", "Data Analyst", "System administrator", "data science", "java developer", "UI/UX designer", "project manager", "graphic designer"]

    # Ініціалізація
    classified = {
        "experience": {
            "years": [],
            "total_experience_years": 0
        },
        "education": [],
        "skills": [],
        "profession": [],
        "other": []
    }

    year_pattern = re.compile(r"\b(19[5-9]\d|20[0-4]\d|2050)\b")  # роки від 1950 до 2050

    for ent in entities:
        text_lower = ent.text.lower()
        label = ent.label_

        # 🔢 Витягування року
        years_found = year_pattern.findall(ent.text)
        if years_found:
            classified["experience"]["years"].extend(map(int, years_found))
            continue  # вже класифіковано

        if label in ["ORG", "GPE"] and any(word in text_lower for word in education_keywords):
            classified["education"].append(ent.text)
        elif any(word in text_lower for word in skill_keywords):
            classified["skills"].append(ent.text)
        elif any(word in text_lower for word in profession_keywords):
            classified["profession"].append(ent.text)
        else:
            classified["other"].append(ent.text)

    # 🔁 Обчислення досвіду
    years = classified["experience"]["years"]
    if years:
        classified["experience"]["total_experience_years"] = max(years) - min(years)

    return classified


def extract_and_classify_entities(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    doc = nlp(text)
    return classify_entities(doc.ents)

def check_for_english(tags):
    eng_doc = nlp("english")
    for other in tags["other"]:
        other_doc = nlp(other.lower())
        if eng_doc.has_vector and other_doc.has_vector:
            if eng_doc.similarity(other_doc) > 0.65:
                return True
    return False

def check_for_profession(tags, profession):
    prof_doc = nlp(profession.lower())
    for other in tags["profession"]:
        print(other)
        other_doc = nlp(other.lower())
        if prof_doc.has_vector and other_doc.has_vector:
            koef = prof_doc.similarity(other_doc)
            print("profession: ", koef)
            if koef > 0.3:
                return True
    return False


def check_education_level(tags):
    education_keywords = {
        "Secondary Education": ["school", "high school", "secondary education"],
        "Vocational Education": ["college", "vocational", "trade school", "community college"],
        "Higher Education": ["university", "academy", "institute", "bachelor", "ba", "bsc"],
        "Graduate Degree": ["phd", "doctor of philosophy", "master", "ma", "msc"]
    }

    # Визначаємо порядок пріоритету рівнів освіти від низьшого до вищого
    priority = ["Secondary Education", "Vocational Education", "Higher Education", "Graduate Degree"]

    combined_tags = tags["education"] + tags["other"]

    found_levels = set()

    for level, keywords in education_keywords.items():
        for tag_text in combined_tags:
            norm_text = tag_text.lower()
            norm_text = re.sub(r'[^\w\s]', '', norm_text)
            if any(keyword in norm_text for keyword in keywords):
                found_levels.add(level)

    # Якщо не знайшли нічого — повертаємо Unknown
    if not found_levels:
        return "Unknown"

    # Повертаємо найкращий рівень за пріоритетом
    for level in reversed(priority):  # починаємо з найвищого
        if level in found_levels:
            return level


# ✅ Функція для обчислення коефіцієнта досвіду
def get_experience_k(result, desired_years):
    """
    Повертає коефіцієнт досвіду: фактичний / бажаний (обмежений 1.0 максимумом)
    """
    actual_years = result["experience"]["total_experience_years"]

    if desired_years == 0:
        return 1.0 if actual_years > 0 else 0.0  # щоб уникнути ділення на 0

    ratio = actual_years / desired_years
    return round(min(ratio, 1.0), 2)



# ✅ Функція для обчислення коефіцієнта освіти
def get_education_k(result, desired_level):
    edu_weights = {
        "Graduate Degree": {
            "Secondary Education": 0.25,
            "Vocational Education": 0.5,
            "Higher Education": 0.75,
            "Graduate Degree": 1.0
        },
        "Higher Education": {
            "Secondary Education": 0.5,
            "Vocational Education": 0.75,
            "Higher Education": 1.0,
            "Graduate Degree": 1.0,
            "_": 0.25
        },
        "Vocational Education": {
            "Secondary Education": 0.75,
            "Vocational Education": 1.0,
            "Higher Education": 1.0,
            "Graduate Degree": 1.0,
            "_": 0.5
        },
        "Secondary Education": {
            "Secondary Education": 1.0,
            "Vocational Education": 1.0,
            "Higher Education": 1.0,
            "Graduate Degree": 1.0,
            "_": 0.75
        }
    }

    education_level = check_education_level(result)
    # print(f"📘 Education Level: {education_level}")
    return edu_weights.get(desired_level, {}).get(education_level, edu_weights.get(desired_level, {}).get("_", 1.0))


def smart_match(tags, required_skills, nlp, sim_threshold=0.6):
    """
    Спочатку точний збіг лем, потім векторна перевірка тільки для незбіглих.
    Лематизація кожного слова окремо, а не всього списку як одного речення.
    """
    # Об'єднуємо всі слова з резюме (skills + other)
    resume_words = tags["skills"] + tags["other"]

    # Лематизуємо кожне слово окремо в резюме
    resume_lemmas = set()
    for word in resume_words:
        doc = nlp(word)
        for token in doc:
            # Додаємо ВСІ токени, крім пробілів і пунктуації
            resume_lemmas.add(token.text.lower())

    # Лематизуємо кожне слово окремо в required_skills
    required_lemmas = []
    for word in required_skills:
        doc = nlp(word.lower())
        for token in doc:
            # Додаємо ВСІ токени, крім пробілів і пунктуації
            required_lemmas.append(token.text.lower())

    matched = []
    unmatched = []

    # Крок 1 — точний збіг
    for lemma in required_lemmas:
        if lemma in resume_lemmas:
            matched.append(lemma)
        else:
            unmatched.append(lemma)

    # Крок 2 — семантична перевірка тільки для unmatched
    for word in unmatched[:]:  # копія списку
        word_doc = nlp(word)
        for res_lemma in resume_lemmas:
            res_doc = nlp(res_lemma)
            if word_doc.has_vector and res_doc.has_vector:
                if word_doc.similarity(res_doc) >= sim_threshold:
                    matched.append(word)
                    unmatched.remove(word)
                    break

    # Результат
    skills_k = len(matched) / len(required_lemmas) if required_lemmas else 0

    print("\n🔍 Smart match (step 1: exact + step 2: semantic only for leftovers)")
    print(f"  ✅ Matched: {matched}")
    print(f"  ❌ Not matched: {unmatched}")
    print(f"  📊 Skills koef: {skills_k:.2f}")

    return skills_k


def analyse_resume(folder_path, experience, english, skills, profession, education):
    print("Let`s start!")
    print(folder_path)
    print(experience)
    print(english)
    print(skills)
    print(profession)
    print(education)
    iterator = 1
    utc_now = datetime.now(timezone.utc)
    formatted = utc_now.strftime("%H_%M_%d_%m_%Y")
    result_name = "evaluation_results_" + formatted
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        result = extract_and_classify_entities(file_path)

        if profession != "Any":
            if not check_for_profession(result, profession):
                continue

        if education != "Any" :
            education_k = get_education_k(result, education)
        else: education_k = 1

        skills_k = smart_match(result, skills, nlp)
        if experience == "Any":
            experience_k = 1
        else: experience_k = get_experience_k(result, experience)

        print(f"{iterator}.{experience_k}, {skills_k}, {education_k}")
        iterator += 1

        k1 = 0.3
        k2 = 0.2
        k3 = 0.5
        k4 = 1.04
        final_score = k1 * experience_k + k2 * education_k + k3 * skills_k
        if english and check_for_english(result):
            final_score = final_score * k4
        elif not english:
            final_score = final_score * k4

        # if final_score >= 60.0:
        print(f"<UNK> {filename} - final score: {final_score:.2f}")

        with open(result_name, "a") as f:
            f.write(f"{filename} - final score: {final_score:.2f}\n")

    os.startfile(result_name)