from googleSheet import Sheet


st = Sheet()

ss = st.createNewSheetFromTemplate(title="Test1")

st.writeValues(sheet=ss, range='A2:B4', values=[[1,2],[2,3],['asd', 123]])

st.writeNotes(sheet=ss, range='A2:B4', rowsOfNotes=[
    ['',"Aasdasdas:12312\nASdAsdasdas:123123\nasfdasdasdsad:123123\nasdasdasd:1312"],
    ['',"Aasdasdas:12312\nASdAsdasdas:123123\nasfdasdasdsad:123123\nasdasdasd:1312"],
    ['',"Aasdasdas:12312\nASdAsdasdas:123123\nasfdasdasdsad:123123\nasdasdasd:1312"]
    ])