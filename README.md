# python-library-mockup
Template repository to create a python library (like julearn)


## Instructions

1. Create a repository on Github using this one as a template.
2. Go to the actions tab and disable the 3 workflows:
   1. Click on the workflow
   2. Click on the 3 dots and select "Disable Workflow"
3. Clone your repository.
4. Create a gh-pages branch:
```
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "Initializing gh-pages branch"
git push origin gh-pages
git checkout main
```
5. Go to Github and activate github pages.
6. Change the name of the library (currently `mockup`)
7. Replace the following tokens with search and replace.

| Token  | Content | Example |
| ------------- | ------------- |------------- |
| `<PKG_NAME>`  | Package name  | `julearn` |
| `<GITHUB_URL>` | Github URL (without .git)   | `https://github.com/juaml/julearn` |
| `<DOC_URL>` | DOCs URL  | `https://juaml.github.io/julearn` |
| `<AUTHOR_NAME>` | Author's name | `Fede Raimondo` |
| `<AUTHOR_EMAIL>` | Author's name | `f.raimondo@fz-juelich.de` |
| `<SHORT_DESC>` | Short description | `FZJ AML Library`

8. Go to https://pypi.org/
   1. login (maybe create an account)
   2. Go to account settings
   3. Scroll down to API tokens
   4. Create a token for all projects, take note.
9. Repeat the previous step but for https://test.pypi.org
10. On your Github repository, go to "Settings" and the "Secrets". Add the respective `PYPI_TOKEN` and `TESTPYPI_TOKEN`
11. Commit the changes.
13. Push
14. Enable the workflows that were disabled in 2
15. This will publish a website on github pages with the documentation. On your Github repostory, go to "Settings" and then "Pages" to see the url.
16. Open the documentation, go to "Maintaining" and follow the instructions to release a version.
17. Go to https://pypi.org/
   1. login 
   2. Go to account settings
   3. Scroll down to API tokens
   4. Create a token for the new project, take note.
   5. Remove the token created in 8.4
18. Repeat the previous step but for https://test.pypi.org
19. On your Github repository, go to "Settings" and the "Secrets". Update the respective `PYPI_TOKEN` and `TESTPYPI_TOKEN`
