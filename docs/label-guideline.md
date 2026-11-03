# Comment label guideline

**Version 1.0, draft for the NLP owner to approve.** Labellers read this before starting. Changing a rule after labelling begins means re-checking the labels it affects, so write every change in the changelog at the bottom.

## The task

Give each comment exactly one label, based only on its own text. Ignore the video, the likes and who wrote it. Also record its language.

## The 6 labels

| Label | The commenter is... | English | Roman Urdu | Urdu script |
|---|---|---|---|---|
| `question` | asking for information | Is this near Mall Road? | Ye kahan hai? | یہ کہاں ہے؟ |
| `request` | asking the creator to do something | Please review Karachi too | Karachi ka bhi review karo | کراچی کا بھی ریویو کریں |
| `praise` | expressing that they like the content, creator or thing shown | Your reactions are the best | Bohat acha content | بہت زبردست |
| `objection` | disputing a claim or fact in the video | It costs 200 now, not 150 | 150 nahi 200 ka hai ab | اب قیمت 200 ہے |
| `complaint` | expressing dissatisfaction with something | The sound is terrible | Awaz bohat kharab hai | آواز خراب ہے |
| `spam` | not saying anything about the content | Earn $500 daily, DM me | Follow back karo | فالو کریں |

## Decision steps

Go down this list and stop at the first yes. The order settles comments that fit two labels.

1. Is it an ad, scam, bot text, follow-for-follow, gibberish, or a bare @tag with no words? **`spam`**
2. Is the commenter unhappy with something? **`complaint`**
3. Do they say something in the video is wrong or untrue? **`objection`**
4. Are they asking for information? **`question`**
5. Are they asking the creator to do something? **`request`**
6. Otherwise, are they positive? **`praise`**
7. Still nothing? Pick the closest label and tick **Unsure**.

## Hard cases

| Comment | Label | Why |
|---|---|---|
| Zabardast! Location kya hai? | `question` | Praise plus a question. The question is what the creator can act on |
| Kya ye halal hai? | `question` | A real request for information |
| Ye kya bakwas hai? | `complaint` | Looks like a question, but no answer is wanted |
| Can you review Karachi next? | `request` | Worded as a question, but it asks for an action |
| Bhai prices barh gaye hain | `objection` | Disputes the price in the video |
| Bohat mehnga hai yaar | `complaint` | Unhappy, without saying the video got it wrong |
| Hands without gloves 😬 | `complaint` | Unhappy about hygiene |
| 😍🔥 | `praise` | Positive emoji only |
| 😂😂 | `praise` | Amusement, unless the text mocks the creator |
| Wah kya baat hai, 500 ka samosa 🙄 | `complaint` | Sarcasm. Label what they mean |
| @ali dekh yaar | `praise` | A tag with words is a recommendation to a friend |
| @ali | `spam` | A bare tag says nothing |
| First! | `spam` | Nothing about the content |
| Pehle comment mera 😎 | `spam` | Nothing about the content |

When words and emoji disagree, follow the meaning of the whole comment. Don't correct spelling in your head into a different word: if you truly can't read it, tick **Unsure**.

## Language field

| Value | Use when |
|---|---|
| `english` | English only |
| `urdu` | Urdu script |
| `roman_urdu` | Urdu in Latin letters, with at most a common loanword such as "video" |
| `mixed` | Roman Urdu and English both carry meaning, or two scripts appear |
| `none` | Emoji or tags only |

## Quality checks

1. **Calibration first.** Everyone labels `infra/label-studio/sample_comments.csv`, then discusses disagreements and updates this guideline.
2. **Shared subset.** At least 200 comments are labelled by two people independently, without seeing each other's answers (`rules.md` 7.4). Report Cohen's kappa with `spikes/labelling/report.py`.
3. **Fix the guideline, not just the label.** If kappa is low for a pair of classes, add a rule and a hard case, then re-check.
4. **Split by reel.** Comments from one reel stay on one side of the train and test split, so near-identical comments can't leak.

## Privacy

Comments are user data (`rules.md` 7.7). Never commit real comments. Keep them in the private store and import them into Label Studio only. Don't export usernames.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-11-03 | First draft |
