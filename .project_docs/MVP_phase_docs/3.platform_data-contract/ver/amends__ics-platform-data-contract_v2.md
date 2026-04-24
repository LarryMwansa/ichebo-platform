Questions For Clarification 
1. If at all I need to add or amend a Handbook type will it be possible to do so?



### 3.3 Controlled relationship type vocabulary

2. On domain prayer I have noticed that type "answers" is directed to domain "prayer" only. Is that only  relationship it has? Or it is open to link to another type?
3. type `has_symbol` I would like to extend to "bible" scriptures and all properties as there is a likelihood that they need `has_symbol` link. Basically all this should have that `has_symbol` relationships:

```js
"journal | prayer | dream | note | bible_note | sermon | governance_class | governance_principle | governance_concept | governance_divine_pattern | governance_narrative | governance_subject | governance_object | governance_mandate | governance_statement

```


### 4.1 Activity object

Is could we add competence, and qualification to `Activity object`


```Javascript
  // Classification
  activity_type: "task | habit | goal | event | campaign | project | programme | reminder | competence | qualification | course | skill",
```

My thinking competence might cover everything between gift, talent, skill, techniques. Please advise?


---

I will add this here I would love to know understand some of those architectural directions and where and at what stage (where feasible) do they get attention? 

1. Platform might work in conditions where internet connective is poor. There might be need for adaptability. Having offline approach that syncs when online capabilities are back. If feasible, this should done in way that is easily maintainable, scalable, cost effective
2. Regarding governance structures such as The Handbook  they should have the capabilities to have local storage that sync to the online storage. This should work without limitations of the internet. 