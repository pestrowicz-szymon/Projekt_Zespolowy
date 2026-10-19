# DOKUMENT WIZJI

## &lt;Testownik AI&gt;

**System generujący quizy jednokrotnego i wielokrotnego wyboru z materiałów akademickich z wykorzystaniem sztucznej inteligencji** &lt;pełny tytuł&gt;

**ZESPÓŁ:**
- &lt;Piotr Staworko&gt; &lt;272913&gt; – kierownik projektu
- &lt;Szymon Pestrowicz&gt; &lt;268496&gt;
- &lt;Radosław Przybyło&gt; &lt;273098&gt;

Politechnika Wrocławska
Wydział Informatyki i Telekomunikacji
Kierunek &lt;Informatyka Stosowana&gt;, &lt;II&gt;, sem. &lt;2&gt;
Specjalność &lt;Zastosowanie Specjalistycznych Technologii Informatycznych&gt;

Wrocław 2026

---

## 1. Wprowadzenie

### 1.1. Ogólny opis projektu

Dokument dotyczy projektu pt. &lt;Testownik AI&gt; realizowanego w ramach zajęć „Projekt zespołowy” przez zespół trzyosobowy.

Niniejszy dokument służy przedstawieniu przeznaczenia tworzonego systemu, jego głównych cech, przyjętych założeń i ograniczeń.

Motywacją projektu jest sposób, w jaki studenci przygotowują się do egzaminów i kolokwiów. Popularną metodą nauki jest rozwiązywanie baz pytań testowych, np. w aplikacji Testownik, powszechnie używanej przez studentów Politechniki Wrocławskiej. Bazy te są jednak tworzone ręcznie: ktoś musi przeczytać wykład, ułożyć pytania i odpowiedzi, a następnie zapisać je w odpowiednim formacie. Dla wielu kursów takie bazy nie istnieją, są niekompletne lub nieaktualne.

Istniejące generatory quizów oparte na AI rozwiązują problem tworzenia pytań, ale nie są zintegrowane z narzędziami, których studenci już używają, i często nie obsługują pytań wielokrotnego wyboru ani materiałów w języku polskim. Projekt łączy oba światy: student wgrywa własne materiały (skrypty, notatki, slajdy), a system generuje gotową bazę pytań w formacie Testownika.

Projekt wykorzystuje duże modele językowe (LLM) jako usługę AI, co jest wymaganiem kursu.

### 1.2. Cel projektu

Celem projektu jest stworzenie aplikacji webowej, która na podstawie materiałów dostarczonych przez użytkownika (dokumenty akademickie, skrypty wykładowe, notatki) generuje z użyciem AI pytania testowe typu ABCD i udostępnia je do pobrania w formacie Testownika.

Aplikacja składać się będzie z trzech części:
- interfejsu użytkownika (aplikacja webowa, React),
- części serwerowej udostępniającej REST-owe API (Django + Django REST Framework),
- modułu AI odpowiedzialnego za ekstrakcję treści z dokumentów i generowanie pytań za pomocą modelu językowego (domyślnie model lokalny przez Ollama).

### 1.3. Zakres i ograniczenia projektu

Projekt realizowany jest w trzech etapach. Wszystkie trzy etapy wchodzą w zakres zaliczenia; etap 1 (MVP) stanowi pierwszy kamień milowy.

**Etap 1 – Obowiązkowe funkcjonalności:**
- wgranie jednego lub kilku plików (PDF, DOCX, PPTX, TXT, Markdown) lub wklejenie tekstu,
- języka pytań (domyślnie język materiału, z możliwością zmiany: polski / angielski),
- generowanie pytań przez AI; model sam decyduje, czy pytanie ma jedną, czy kilka poprawnych odpowiedzi,
- pobranie bazy pytań w formacie Testownika (archiwum ZIP),
- obsługa skanów i obrazów (OCR),
- brak kont użytkowników; dokumenty przetwarzane są tymczasowo i usuwane po zakończeniu sesji.

**Dalszy rozwój (poza zakresem zaliczenia):**
- rejestracja i logowanie użytkowników,
- biblioteka: Użytkownik → Kurs → Dokumenty,
- generowanie pytań z wybranych rozdziałów lub stron dokumentu,
- generowanie quizu z jednego lub wielu dokumentów należących do kursu,
- rozwiązywanie quizów w aplikacji: tryb testu (jedno przejście, wynik, przegląd błędów, „powtórz tylko błędne”) oraz tryb nauki w stylu Testownika (powtarzanie pytań do N poprawnych odpowiedzi),
- historia podejść dla każdego quizu.


**Ograniczenia:**
- jakość pytań zależy od jakości materiału i modelu językowego; system nie gwarantuje poprawności merytorycznej.
- szybkość generowania pytań jest ograniczona szybkością sprzętu użytkownika

### 1.4. Rozwiązania konkurencyjne

**Testownik** – aplikacja (desktopowa / webowa, różne implementacje) popularna wśród studentów PWr, służąca do nauki z baz pytań zapisanych jako pliki tekstowe. Bardzo dobry tryb nauki z powtórkami, obsługa pytań wielokrotnego wyboru. Brak jakiegokolwiek generowania pytań – bazy muszą być przygotowane ręcznie. Nasz projekt jest dla Testownika uzupełnieniem, a nie konkurencją: generuje bazy w jego formacie.

**Quizlet** – popularna platforma do nauki z fiszkami i testami, z funkcjami AI tworzącymi materiały do nauki z notatek. Rozbudowana, ale nastawiona na fiszki; pełne funkcje AI są płatne; brak eksportu do formatu Testownika.

**Quizgecko** – generator quizów AI z tekstu, plików i stron WWW, z różnymi typami pytań i eksportem. Model freemium, interfejs i rynek głównie anglojęzyczny, brak integracji z narzędziami używanymi na polskich uczelniach.

**RemNote** – aplikacja do notatek z powtórkami rozłożonymi w czasie; potrafi generować pytania wielokrotnego wyboru z PDF i notatek wraz z wyjaśnieniami. Wymaga przeniesienia całej nauki do własnego ekosystemu; brak eksportu do Testownika.

**NoteGPT** – narzędzie AI generujące pytania wielokrotnego wyboru z tekstu i PDF z wyborem liczby pytań i poziomu trudności. Proste, ale bez biblioteki kursów i bez trybu nauki w stylu Testownika.

| Cecha | Testownik | Quizlet | Quizgecko | RemNote | NoteGPT | **&lt;nazwa_kodowa&gt;** |
|---|---|---|---|---|---|---|
| Generowanie pytań przez AI z dokumentów | nie | tak | tak | tak | tak | **tak** |
| Eksport do formatu Testownika | – | nie | nie | nie | nie | **tak** |
| Rozwiązywanie quizów w aplikacji | tak | tak | tak | tak | tak | **tak (dalszy rozwój)** |
| Interfejs w języku polskim | tak | tak | nie | nie | nie | **tak** |
| Działanie bez konta | tak | nie | nie | tak | nie | **tak** |
| Możliwość uruchomienia z lokalnym modelem AI | – | nie | nie | nie | nie | **tak** |
| Darmowe | tak | częściowo | częściowo | częściowo | częściowo | **tak** |

---

## 2. Własności produktu

1. Aplikacja będzie definiować REST-owe API (dalej: API); interfejs użytkownika komunikuje się z serwerem wyłącznie przez API.
2. Aplikacja będzie przyjmować dokumenty w formatach PDF, DOCX, PPTX, TXT, Markdown oraz tekst wklejony bezpośrednio.
3. Aplikacja będzie generować pytania testowe ABCD na podstawie dostarczonych materiałów przy użyciu modelu językowego.
4. **Model AI sam decyduje dla każdego pytania, czy ma ono jedną, czy kilka poprawnych odpowiedzi** – np. fragment typu „metodami X są a, b i c” naturalnie prowadzi do pytania wielokrotnego wyboru.
5. Pytania generowane są w języku materiału źródłowego (polski / angielski), z możliwością wymuszenia innego języka.
6. Przed pobraniem użytkownik widzi podgląd pytań i może usunąć lub ponownie wygenerować pojedyncze pytanie.
7. **Aplikacja eksportuje pytania w formacie Testownika** (archiwum ZIP z plikiem `.txt` dla każdego pytania), dzięki czemu wygenerowane bazy można od razu wczytać do narzędzia, którego studenci już używają.
8. Generowanie odbywa się asynchronicznie – użytkownik widzi postęp przetwarzania.
9. (Dalszy rozwój) Konta użytkowników, biblioteka kursów, generowanie quizu z wielu dokumentów kursu, rozwiązywanie quizów w trybie testu i nauki, historia podejść.

Nowe, ważne funkcje niedostępne w rozwiązaniach konkurencyjnych: eksport i import baz Testownika (pkt 7, 10), automatyczne wykrywanie pytań wielokrotnego wyboru (pkt 4), możliwość działania z lokalnym modelem AI bez wysyłania materiałów na zewnątrz (pkt 10).

### 2.1. Format Testownika

Każde pytanie zapisywane jest w osobnym pliku tekstowym (`001.txt`, `002.txt`, …), pakowanym do archiwum ZIP:

```
X1100
Treść pytania
odpowiedź a
odpowiedź b
odpowiedź c
odpowiedź d
```

Pierwsza linia zaczyna się od `X`, po którym następuje klucz odpowiedzi – po jednej cyfrze na każdą odpowiedź (`1` – poprawna, `0` – błędna). W powyższym przykładzie poprawne są odpowiedzi a i b.

---

## 3. Wymagania funkcjonalne

| ID | Wymaganie | Etap |
|---|---|---|
| WF-01 | Użytkownik może wgrać jeden lub więcej plików PDF, DOCX, PPTX, TXT, MD lub wkleić tekst. | 1 |
| WF-02 | Użytkownik może wybrać język pytań; domyślnie jest to język materiału. | 1 |  
| WF-03 | System wyodrębnia tekst z dokumentów i generuje pytania za pomocą modelu AI. | 1 |
| WF-04 | Model AI decyduje dla każdego pytania o liczbie poprawnych odpowiedzi (jedna lub więcej). | 1 |
| WF-05 | Dokumenty dłuższe niż kontekst modelu dzielone są na fragmenty, a pytania rozkładane proporcjonalnie. | 1 |
| WF-06 | System pokazuje postęp generowania. | 1 |
| WF-07 | Użytkownik może pobrać pytania jako archiwum ZIP w formacie Testownika. | 1 |
| WF-08 | Użytkownik może się zarejestrować, zalogować i usunąć konto. | Dalszy rozwój |
| WF-09 | Użytkownik może tworzyć kursy i przypisywać do nich dokumenty oraz quizy. | Dalszy rozwój |
| WF-10 | Użytkownik może wygenerować quiz z wielu dokumentów jednego kursu. | Dalszy rozwój |
| WF-11 | Użytkownik może edytować treść pytań i odpowiedzi. | Dalszy rozwój |
| WF-12 | Użytkownik może rozwiązać quiz w trybie testu (wynik, przegląd błędów, „powtórz tylko błędne”). | Dalszy rozwój |
| WF-13 | Użytkownik może rozwiązać quiz w trybie nauki (powtarzanie pytań do N poprawnych odpowiedzi). | Dalszy rozwój |
| WF-14 | System zapisuje historię podejść do quizu (data, wynik, błędne pytania). | Dalszy rozwój |
| WF-15 | Pytania wielokrotnego wyboru są oznaczone w interfejsie i oceniane metodą „wszystko albo nic”. | Dalszy rozwój |
| WF-16 | Użytkownik może trwale usunąć dokument lub kurs. | Dalszy rozwój |

## 4. Wymagania niefunkcjonalne

- **Wydajność:** wygenerowanie pytań z dokumentu nie powinno trwać przesadnie długo.
- **Limity:** maksymalny rozmiar pliku 100 MB.
- **Wymienność dostawcy AI:** moduł AI jest oddzielony od reszty systemu.
- **Użyteczność:** interfejs w języku polskim, działający w aktualnych wersjach popularnych przeglądarek.
- **Dokumentacja:** API udokumentowane (OpenAPI / Swagger).

## 5. Wymagania inne

- **Technologie:** React (frontend), Django + Django REST Framework (backend), PostgreSQL (baza danych), Ollama.
- **Repozytorium i współpraca:** Git (GitHub), przegląd kodu przez pull requesty.

## 6. Ograniczenia

- Jakość pytań zależna od modelu AI. 
- Backend lokalny (Ollama) wymaga maszyny z GPU.

## 7. Użytkownicy

- **Student:** chce szybko zamienić swoje materiały w bazę pytań do Testownika, bez zakładania konta.
- **Użytkownik zarejestrowany (Dalszy rozwój):** student, który przechowuje materiały i quizy w bibliotece kursów, rozwiązuje quizy w aplikacji i śledzi swoje wyniki.

## 8. Przypadki użycia

| ID | Aktor | Przypadek użycia | Etap |
|---|---|---|---|
| PU-01 | Student | Wygeneruj bazę pytań z wgranych plików | 1 |
| PU-02 | Student | Przejrzyj pytania, usuń lub wygeneruj ponownie wybrane pytanie | 1 |
| PU-03 | Student | Pobierz bazę pytań w formacie Testownika | 1 |
| PU-04 | Użytkownik | Zarejestruj się / zaloguj się / usuń konto | Dalszy rozwój |
| PU-05 | Użytkownik zarejestrowany | Zarządzaj kursami i dokumentami | Dalszy rozwój |
| PU-06 | Użytkownik zarejestrowany | Wygeneruj quiz z wielu dokumentów kursu | Dalszy rozwój |
| PU-07 | Użytkownik zarejestrowany | Rozwiąż quiz w trybie testu / nauki | Dalszy rozwój |
| PU-08 | Użytkownik zarejestrowany | Przeglądaj historię podejść, powtórz błędne pytania | Dalszy rozwój |

**PU-01 – scenariusz główny:**
1. Użytkownik wgrywa pliki lub wkleja tekst.
2. Użytkownik opcjonalnie wybiera język.
3. System wyodrębnia tekst, uruchamia zadanie generowania i pokazuje postęp.
4. System wyświetla wygenerowane pytania (PU-02).
5. Użytkownik pobiera archiwum ZIP (PU-03).

**Scenariusze alternatywne:** nieobsługiwany format lub zbyt duży plik → komunikat o błędzie; błąd generowania → możliwość ponowienia.

## 9. Podział zadań (wstępny)

| Obszar | Zakres |
|---|---|
| Frontend | Interfejs React: wgrywanie plików, podgląd pytań, (Dalszy rozwój) biblioteka, rozwiązywanie quizów, historia |
| Backend | Django + DRF: API, zadania asynchroniczne, limity, (Dalszy rozwój) konta, model danych, biblioteka |
| AI i formaty | Ekstrakcja tekstu z dokumentów, prompty i integracja z LLM, podział na fragmenty, eksport/import (Testownik), backend Ollama |

## 10. Osoby odpowiedzialne za zadania

| Osoba | Odpowiedzialność |
|---|---|
| &lt;Piotr Staworko&gt; | &lt;Backend&gt; |
| &lt;Radosław Przybyło&gt; | &lt;Frontend&gt; |
| &lt;Szymon Pestrowicz&gt; | &lt;AI&gt; |

---

## 11. Harmonogram prac (wstępny)

| Tydzień | Zadania |
|---|---|
| 3 | Stworzenie wizji i harmonogramu projektu. Nadanie nazwy. Przygotowanie infrastruktury (repozytorium, konto u dostawcy AI, środowisko). |
| 5 | Stworzenie zarysu strony, wstępnych endpointów API |
| 7 | Przygotowanie modelu AI z którym można komunikować się przez stronę |
| 9 | Model AI jest w stanie odczytać przesłane pliki |
| 10 | Model jest w stanie wygenerować pytania |
| 11 | Pytania są generowane w formacie testownika |
| 12 | Testy aplikacji |
| 13 | Gotowy produkt + raport końcowy |

---

## Źródła

Do uzupełnienia w trakcie przygotowywania projektu i zbierania wiedzy
