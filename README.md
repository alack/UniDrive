# UniDrive
Unifies your drives

## test

fill config file based on `config.sample.json`. config file name have to be `config.json`
```bash
python ./test.py
```

At first time, dropbox and google drive try oauth2 dance. login page will automatically open. after login copy address starting with 'https://localhost' and paste to console.
it will create token json file in project root directory. after first time it will use json file to load access token. when access token expires it will use refresh token to get new access token
