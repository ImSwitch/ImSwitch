# ImSwitch

[![DOI](https://joss.theoj.org/papers/10.21105/joss.03394/status.svg)](https://doi.org/10.21105/joss.03394)
![image-sc-badge](https://img.shields.io/badge/image.sc-community_partner-pink.svg?logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAAVYAAAFCCAMAAACdNgU8AAABs1BMVEUAAAACnbJ1b7XtU3QCnbJ1b7XtU3QCnbJ1b7XtU3QCnbJ1b7XtU3QCnbIZlLNgf5l1b7XtU3QCnbIojrN1b7XtU3QCnbJ1b7XtU3QCnbJ1b7XtU3QCnbIPmLJ1b7XtU3QCnbJ1b7XhVnvtU3QCnbJ1b7XtU3QCnbJPfrR1b7XtU3QCnbJ1b7XtU3QCnbJ1b7V%2BbbDtU3QCnbJ1b7XtU3QCnbIRmK4So7cflKoiqbwuj6Yxr8A8hrQ9i6NBtsVLhp9RvMpYe7RagZteqsZhhLlhws9pfZdxyNR1b7V4eJN9bbF%2BeLqBztmDqMuEbK2Gc4%2BGgb6MaqmPisOQ1N2TaKWVb4uVutWYk8ibZqGgnMyg2uKiZZ2kaoeppdGqY5mw4OexYZWxrtWyZoS5X5C6t9rAXozA5%2BzBYYDDwN%2FIXIjIobTKvtvLyePPWoTQXHzQ7fHSco3Sep7Uh5%2FU0ujXWIDd2%2B3eV3zeWHjf8%2FXl5PHmVXjoaonpwtPtU3TuXn3u7fbvaYXv%2Bfrwc47yfpfziZ%2F0lKj1nrH2qbr29vr3tML4v8v5ydT71Nz83%2BX96u7%2B9Pb%2F%2F%2F9YhNSnAAAANXRSTlMAEBAQICAgMDAwQEBAUFBQUFBgYGBgcHBwgICAj4%2BPj5%2Bfn5%2Bvr6%2B%2Fv7%2B%2Fz8%2FP39%2Ff3%2B%2Fv74s6yQIAABSySURBVHja7Z39QxPZ9cbHZIMobIsWFg0WpIg2LJhGEkX9itVWdwSqqFhf2Qoiui2y7ZdFxHYSXuQ9JPMnV1EwL%2FNyz73PvXNJ8%2FwqZoYPkzPPPefccw1DnQ4eP3UmIJ06ftCoSB04fjYVqM4eP1B5VI%2BeSwWuc0cr7VE9mdJCpyrqgT3wfUoTfV9JXLWh%2BpFr5VA9kdJIJyqF6uGUVjpcDQFSjFZlUP02pZm%2BrQisp3TDeqoisKa0U%2FWFVX1pueg7%2FbB%2BVwFYj%2BuH9XgVaxVrFWsVaxVrFWsVaxVrFasSrDX1VaxYrDXHTietT%2BppO6IRu9rm1lgs1hqt25dYazqsAiWa9GAaisbNXfW2R%2FYb1nCLVaKeQxpQjfaaRWoP7SusTUmrXIE%2FsLXdZql6o%2FsHa32P5aiAudb2mg6K1%2B0PrDWnLTcd0Y%2FqR8Ui%2BmMNtyRdqVrJmgBfVnHTVa0hzbE2JSwvdQWHtd30UG%2BjzlgPdVk%2BCmxxUGd6q7tOV6zhDstXiaCwxkw%2FdUa0xOoVVL%2BqJRiqjSaDor%2FVjurVaYtJybBu76sC%2FZ9mUPvGLVZ1BLK6Mvch1vN3LIICWMRGzH2I9eYchWoQJqtz%2F2G9Mm0RdUQ3c6Uf1r5nFlkJ1W%2Bt7n2G9fwti0eKTVazKQXrxRtDXLpx0eeDr89xUVWcGgj1ysB64YnNrScXvILqK4tXSk1WqykB6%2BVFW0CLl12D6gNLQPX6mSsS1gvvbCG9u%2BASVOdEqKo0WTEZWIdsQQ2JrFTd1aSduSJhfSeK9V35Z14at4SlLDUQl4H1gi2s0ihw%2FoGFkCKTFTVlYO0Xx9pf%2FImCQfWrajQzV0FivTJtoXQ68EqLLlj7xi2gFJisWlN%2FrLT0nxb1l5j%2BWG%2FOWWAdk021wdQdq8BKNTCTFYprjpUn%2FcegNp3MlXKsnOm%2FoE1WpFdrrNenZVGVmxpoNzXGmv2nJVES6y91pr5YcyuWVCX0MVcKsa6lLcmSlhpoNHXFurVgSZcskxXq1RTr9rKlQh26mCslWPMrliJJaXKJmFpi3UiroirHZHXqiDW7YClUkx7mSjbW3LKlVBKaXOLaYc2vWqoFN1nNpm5YN9PKqcKbXPjMlUSs2SUrCIHrL62mVlhzH6yAVK%2BBuZKENb%2BWDoqq1RN0MkAa1s0FK0ABTVaDqQ%2FW7LIVqICpgbg2WNWtVOWbrKipC9YAgyq8%2FsJvrsBY4em%2Fle1ProL6twKlBqiVluGxqdmJx3Cs8PTfcm43siwFYLKIbSyDU5%2FvNTMKxQpfqS5kCz6cxjWh3lwNzu%2Fd7OxDHFZ0%2Bi%2B9UWwvlDe5ECsts4V3OzWIwQpP%2F63mS66wothkEdtYHhbf7foEACs8%2Fbe8XR5jaN%2BGNsXmKlN6v5k%2FCWLNr6GD6pajdVNafyG2sUwwbpRgx4pO%2F6XXXP58CypNFq3SMrgOxrqNTv%2Bt5F1NscImF2KlZcrGYt0CP6rLWY%2F34rI6k9VNonrPxmLdBAfVTe8crrLUgIi5EseaxVJdy%2Fss41YVmSxiMuCxDcWah0aADzn%2F7Bjtgh1qzNVgBosVmQJcyjJ1cihJDRArLRM2FGsOaKo2GVPkSkwWLRkwvI7FintYV%2FOs5RxiNG8KyFyJYEVF1uWczS5aQZeryUUoGSCMFWQDFrI2RfJNVjPAXAlghWQCStJ%2FLFUdyfUXorkatcFYEaF1JU%2BlSjVZ5CaXVuFkgBhW8WSgQ%2FqPpQlBqsmqhZirALE6p%2F8YREvu9Eg1V7ZmWNNreU6qUk0WsY1lBo9VqCK4krP5JbH%2BAjJXAlg3BIJq1hZRTlr9RbTSAsC6LX2lqtxkEc3VmI3AelFofc6e%2FmMwWZJSA%2B0oc0XBmloErAeWtm2AtqSYLGIy4LWNwfpEKMR9dlV5GyIp9RecuSJhvWgLP65ZDFVqYD%2BmqtLCgzV1QyjEfQoBNkp4k0VsY3lsw7CmbiyKVQjXYFjx9RekuSJiTV34YbJQ1GkWWzCs8CaXCCwZwIG1dEhwQKFVQv2lE2muBLGmHgQVBMipgSNKKi0grOdp49c%2BlF18ZuLhJ41NrQdrsgBtLECsKeJYq%2BIMS2Z0sODVOkvEiqy%2FgM2VMNYUbbDVcmFr7VhpQmiexpXY5FKjoNICw3qV1wvMDzvc73owJotYacnIx5qizWFd2KM66HjHr0njSkCpAbi5AmC9xGUGnKl%2BWmpTQuwSxmRh2liwWFO0CbfpnWTL%2BrBHzj0jy2Q1QczVjK0EK9FkrXy65qj3t4w5xNKaXFxSA8BKCxBr6iZ5qTXLuCNPickitrHMq8JKN1kP%2FQ33rJTUQI0ac4XBSkwNbE4xZd4yEkzWacmVFihWosn69zDbb8AUYkWbXGplmCsQ1j7Sr%2Fac2cpMwVMDPXIrLVispNTA2wHCa3cWbbKOCbWxzKrFSjFZj2iviHXs41pisuSYKxTW1HXm3%2BsNcabE4AR2CdsmUGmZUo01xXxEw13y1JPhGWQUKDRZ1Ln388qxspqslzzjZDxThlSsXfzTWGzlWFNsh1%2B8HzC5NLaOanEpMFnk0awZ9Vj7mN5aP%2FLOP3JPGZK77RPco%2B5m1GNlMllvBQZLuaQMObaItvDOvR8NAOt5htTAiMjALuf1LMfozc8mi2d62Lx6rAwm640pqPL1LNeGmxbeUXfD6%2Bqx%2BqcGbotiLU0Zcs7eTXDPZRycVY%2FVr%2F7ywgSoIGXIf0rMIf4J7azFi0kYVp8mF15zVfbi%2BPyLiczebREZdznGFAkWcVi9UwNPTZB2UoZCs3dPCw0SZiteXMZx9TJZv5g4Df9DbFtYl9jIW6bixX0cVq%2F6y4iJ1MgvglgFr%2B9fvFi8gMPq3uTykwnW0%2FdBYmUoXgwBH9dxeeaqVAPPg8TKULwARtc%2B0UoLRbffcGJtE3plsRYvfgaGgTvClRZSiH3LhbWJ6zBMcvECyNXZZD01ZelHnhBbI3AGDqV4AeR6U0YywCvEviBT7RE7V4RQvFjsl2myRkyZuvuGHgO4T22jFi%2F%2BdhGE9Qqm0kLRo7fkTAt3UoC8np38AWMJSusv72%2Bb0vWcEGLrhQ4ZJBYvvgTZnX1sf75G0e8PF%2BvXKsxVWYh9Se0bFDsFg6Pf%2BTXtE2tLO3BaYJUWktliC7EdvP1XoinD9UHSx7WXdeGFk%2FxtLELr2bcUqobR2Iu9vvd6doz0Wb2h8u7GJkXmqnw96xNik8U9WLVgrl4pw3naR0WdWpy7RNpYhNazP3nmWUv7hkPt4Ou7pwwfkj4n7tiPX4%2BttGBShgmnLUR1MfD1R51D7AztUxqct490gCst4inDpNsMjMY4OBI4hthh0mfEXO61JinYxoJez7a5T8AIRcHXd0gZTtA%2BIeJ2ry1KzZVfyrDLexhWpBN8%2FdL1bIZmrlpd7zSckJ8MYE0ZJvyPzKjrRofYokjwWNhc7eqIYnPlmjJMss0cRpvYwpThFO2%2FNnvdZ5eMSgt9PdvBOrsx1IoOsV9ShuvEwBr3vM1DapIB3inDLsoJTxG02br3enZ2ZmyY%2BL%2FqvO%2FydwNm4OqM0Kbj%2FyH4e35Tjz3R8%2FPfdhB8l9EQAWtT8v3TgKmO%2BMyVISaIBvciERhsvJEVan3PThJjJFCsb32G93Gf6JkZBd9prI4Fak3HXjUjwFftjz7D%2B0Q26M3eA99su2%2BIDbcUZDPfB%2FayHXhftnkMeKLnzlGpSPVGfYJqoqSx4VEwWF%2B47tDHjEKkmj3%2FENvg4QW7HIrwdwOgetdnrkxEfM505jE6xNa6fP87XLbmqTdbb3yG90GmH8wOg%2B%2B61clstSRd%2B8dV598e%2BQzvQ41CfI0OsWXL7SMJz41kas3WW5%2B5MjRz5TEKcX0MHQmKHtjwad9NTwrN1nOfMUjIUYjzD7H33l3AtaaHoQL%2BQlWIvf3ee3gf5ETPgjLQsCSu4STb%2FmdF69mXPhOS0XOmbex6tnOXag9rI8wvKkLsSGnLeEmz0K9IrUbX%2FrLTn%2FTOuyMEup794mDbCO1wP8kPsWVNOdchHXH9973QzgJDbPxLPpii988lh9inZZecPg%2Fq4bzhBXYKF2J3clqniV2xb6WG2AGHRqdbsJ7jIa9IAAuxn8rwNfTeeJkpQ6dtO3N9MK79ix5gYevZj2bgGM9eDmnr2duOl3uG2ypz2YsrKmXYUNQmRgqxcrC6tI5dwXHt9zZbkJRh1DCSFp%2BkpAxHXC72CrgTccin%2FXYMgpV%2Fa6eElKFrO951INd3PquDjLDZ6iTaK8nr2aeuV5o7j8N6w3fZJZoybC1oFeUKsdCU4YBHs%2FMthY%2BrcMpQKAjsjE7%2FD3B54rlhD2eyUvcZpksIrWebBbF%2BOqgSlmS%2F7XmpcWVmQDxlWGsYPfxQP%2BSgGSCfHTpAk8U4FYk3ZdhLTLQUaSGLzQCN%2BFxvGod1kXXc1ATnG8vgtQLpDXSS3XfX000Y1knm6WhTPL%2FJTjNGgofqch6dAfKf4YEzWexYeZ7X9rLNY8xU4RmgAYbNuncCwLpO%2FqV2e8jpWYG080n1Ik1jTFt1L6nHao9ymNaSzWOsWoFngO4yXXc8AKzUKBAv2zzGrC14BohxwsRV%2FbHWlW0eY1bWM8ku1MaixGRJxBpz3aEvhpUnyT7APLXjlnKsjznM1a6IJmsTnAFiH5CGqb8QsGboK4HizWOC%2FkogA3SbMAnlgWKso1zmymGHvngUoCbZX1IufUUp1lnaw9pctnmMlg9g%2BfqwrmdHSJceV4qVtibvdt2hz6gNYAboX7RLX1eIdYrXXBHb2%2FbWWXk2d8IQYkdztCnUgCaXSTkr106HVlxiv8Aq4435hvzBdepJireUYUVMPyCarG3WoO8TniZsO0%2Bc792nCGuGLxngNlcGZLKYUob3OE5SfKYIK2b6QRcsMcCeMvyyaZI4Of2KEqxEc%2BW297UGb7J817NTXId9vVKC9R53MqBYxLLWGuU4MueU4RTnmTTXFWB9LWqu5Jos95Th8DzvuVSC9ZdJvLlq99rxCspms6UMi6a9Ek3WHelYiaMQPfdoE5sGsjSudmZizxQMT5TsQFFpsiYVmSvpJuvr7c5MfNRMRvS46nHJWImjEH1GixA3EmzaMOUtdSZrEm2uGvxGXxBNVh7HlYh1WirWYZC54qy%2FrAWG1fr7ZIGe3IBiJSYDan2xhmmpAZeOAQ7lyM0Kxd%2BUny%2FjsALNFafJ%2BoDCukbFWurvFi%2FDsI5CkgGS6y9sbyyOo%2F9Kkmg%2Fo7AS50w3s03Bov1uSxisPMfUlfq7P4KwIuZMG6L1F4TJyvGdqFryuD7BYJ1CJQNUpgacAsCaxadVzsNPPbGuo81VQCZrk%2FtE1QUZWFFzpoXrL0Imi%2FNE5c%2FK47HC5kw7T0iWmxrYC6orloiyeKwyzJVikyVyorIkrKBKi9uEZGn1l8KgumAJag2OlVZp6TZoItZfNjigbi9bwtpCY5VkrpSZrPyKBRA6CADaWLxFbHIh1l9s0aDq6EHEscozV5KbXHa0tQCBaqXBvhVaaVFdf8ktWyCtgLE%2BhlZalDa55FctmLJYrFLNldwml400jmrpJUWxykoGSE8NCK1UfVchglhfyzVXvCbLNzWQ%2B4CEWl6YEMMqodKiosmFO%2F3nlj%2FPY7GOSUwGyGty2UxjqTp8OYSwKjBXeJOVXbZkP6uCWOVUWqQ2ueRWwFCtVafVsghWzImerCaL9tZybnLJr4G%2F%2F9ay85pOBKsacwU0WaiV6tc%2FntuXghnrX9elt7FAm1zK6y%2Fb6KCaXnPNljFjvbZ7jh%2BnuWo1RCXW5JKHB9UVD3fMjrX0qNTHyswVov6ygQ6qS54ejoK16KhU5ImecuovBQntLDqopn06PWhY945KpU5sjRsIEZtcdoe55dBB1VrzK0EQsZrm8NjU7OtR6nSZOgjWMHWSy%2FJmNrsFD6rL%2Ft0IZKxcihkYtVjBa4GlZq4GawSElW9cHjSoslV2lWCNoqhSm1zgWmWs66rAijBXnCZLyUo1IKyNOKo8J2nAgir7RnAVWLsNpNqCCqqkJk8FWOugWMPJQKiu0Jpl5GPtNLA6FkRQpTYiSsfaGwFjVW%2ByFuh7EqRjjaKpCh77gEz%2FBYc1HoJjJZ9WJlar5uqbl421EU9Vpcla4uzulow1ZsiQqtRAmnujl2SstVKwKjJZq%2FzbvORibTfkqEmFqRLZjCQVa29IElb5qYEFsX3JUrFGZVGVbbLSG7atLda4IU8dMqn%2Bv%2FDeWZlYGyRirZH31hq%2FNGRrjDVmyJQskzV91fdEy2CxRqRiDUtJDcztDLrVGWurIVcy6i8PPk9g0xirPHMlzWSN784J0xhrs2yqYufCOgTVryND9cUaN%2BQLarJuFQwM1RdrnQKswNTAs6Kxltpi7TRUCGWyXpUMX9QWa0QJVkz9Za7sHExdsUbVUIWkBu6UT2G%2BLIz1vgys8s0VzGSNO84KfieK9aIMrI2qqIrWX6ZdJtr2q3pYKVi7DXVqE16pOuqGEFXmUXgkrHUKsQqYrAdeo%2B37%2BePA4lBKBtZ2Q6V4m1zG%2FQ7AvfzDEJf6SUOcmbH2RpRipW4y%2Fpr%2B00LXdDNXAiZr7tb51D7DGg8pxkpvcnnQl0rtN6wNqqlSTdarK6nUvsMaM9SLkhqYu55K7UOstQFgJdRf9AmqJKztRhBq4kr%2FaaHfxLRKBnCkBhL1Kf102KiLa2euCCYrecwwtMRqGNHe4CstnPWXtrChLVYj1K5NMoDU5NJVs%2FNTumI1jNpYcJ0BvKmBxJEvP6QvVsNoiGuQDySEgWTL3s%2FojNUIOYfY7lCgWN1SLh1hY39gNYxIuy6O1e957TpU%2BBOaYzWMupIQG28wgtex0vdWoqn4B7TH%2BhFsZ8H3v9HQQuGOZFFQDRv7DuvHGNsQ7YzFOqONEUMbhZtOf04QJDqOlP%2FrvsCqrcL1Yed%2FqGKVoirWKtYq1irWKtYq1irW%2F2Ws31exytAZ%2FbBWAFXjhHZUz1YC1qPaYT1ZCVgPaIf1aCVgNU5qRvVcRVA1vtEM6%2FHKwKrZS%2BvsgQrBeuBs1bTK0MFz1fdVZXM9YVSSDp6tPqtS4qsO760zB42K0zdB%2B9czR42K1IFvT5wJSie%2F%2B0bhb%2FpfIARAbJF5UKEAAAAASUVORK5CYII%3D)


``ImSwitch`` is a software solution in Python that aims at generalizing microscope control by using an architecture based on the model-view-presenter (MVP) to provide a solution for flexible control of multiple microscope modalities.

## Statement of need

The constant development of novel microscopy methods with an increased number of dedicated
hardware devices poses significant challenges to software development.
ImSwitch is designed to be compatible with many different microscope modalities and customizable to the
specific design of individual custom-built microscopes, all while using the same software. We
would like to involve the community in further developing ImSwitch in this direction, believing
that it is possible to integrate current state-of-the-art solutions into one unified software.

## Installation

### Option A: Standalone bundles for Windows

Windows users can download ImSwitch in standalone format from the [releases page on GitHub](https://github.com/kasasxav/ImSwitch/releases). Further information is available there. An existing Python installation is *not* required.

### Option B: Install using pip

ImSwitch is also published on PyPI and can be installed using pip. Python 3.7 or later is required. Additionally, certain components (the image reconstruction module and support for TIS cameras) require the software to be running on Windows, but most of the functionality is available on other operating systems as well.

To install ImSwitch from PyPI, run the following command:

```
pip install ImSwitch
```

You will then be able to start ImSwitch with this command:

```
imswitch
```
(Developers installing ImSwitch from the source repository should run `pip install -r requirements-dev.txt` instead, and start it using ``python -m imswitch``)

## Documentation

Further documentation is available at [imswitch.readthedocs.io](https://imswitch.readthedocs.io).

## Testing

ImSwitch has automated testing through GitHub Actions, including UI and unit tests. It is also possible to manually inspect and test the software without any device since it contains mockers that are automatically initialized if the instrumentation specified in the config file is not detected.

## Contributing

Read the [contributing section](https://imswitch.readthedocs.io/en/latest/contributing.html) in the documentation if you want to help us improve and further develop ImSwitch!
