# Machine Learning Cyberattack Simulation

## Startup

To get started with running this simulator locally first clone it down:

```sh
git clone https://github.com/Capstone-Group12/ml-ca-sim.git
```

After cloning it down make sure you install the packages:

```sh
pnpm i
```

## Development Commands

To build all apps and packages, run the following command:

```sh
pnpm turbo run build
```

You can build a specific package by using a [filter](https://turborepo.com/docs/crafting-your-repository/running-tasks#using-filters):

```sh
pnpm turbo run build --filter=web
```

To develop all apps and packages, run the following command:

```sh
pnpm turbo run dev
```

You can develop a specific package by using a [filter](https://turborepo.com/docs/crafting-your-repository/running-tasks#using-filters):

```sh
pnpm turbo run dev --filter=web
```
