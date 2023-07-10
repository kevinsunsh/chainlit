import { execSync, spawn } from "child_process";
import { join } from "path";
import { readdirSync, existsSync, unlinkSync } from "fs";

const ROOT = process.cwd();
const E2E_DIR = join(ROOT, "cypress/e2e");
const CHAINLIT_DIR = join(ROOT, "src");
const FRONTEND_DIR = join(CHAINLIT_DIR, "chainlit", "frontend");

const candidateFiles = ["main.py", "main_sync.py", "main_async.py"];

const runLocal = [
  "cot",
  "global_elements",
  "scoped_elements",
  "update_message",
  "remove_message",
];

function cleanLocalData(testDir: string) {
  if (existsSync(join(testDir, ".chainlit/chat_files"))) {
    execSync("rm -rf .chainlit/chat_files", {
      encoding: "utf-8",
      cwd: testDir,
      env: process.env,
      stdio: "inherit",
    });
  }
  if (existsSync(join(testDir, ".chainlit/chat.db"))) {
    unlinkSync(join(testDir, ".chainlit/chat.db"));
  }
}

export async function runTest(test: string) {
  const testDir = join(E2E_DIR, test);
  const variants = candidateFiles.filter((file) =>
    existsSync(join(testDir, file))
  );

  const runFiles = async (localDb = false) => {
    for (const file of variants) {
      let childProcess;

      cleanLocalData(testDir);

      console.log(`Running spec "${test}" with chainlit file "${file}"`);

      if (localDb) {
        console.log("Running with local db");
      }

      try {
        childProcess = await runChainlit(testDir, file, localDb);
        runSpec(test);
      } finally {
        childProcess?.kill();
      }
    }
  };

  await runFiles();

  if (runLocal.includes(test)) {
    await runFiles(true);
  }
}

export async function runTests() {
  for (const test of readdirSync(E2E_DIR)) {
    await runTest(test);
  }
}

function runCommand(command: string, cwd = ROOT) {
  return execSync(command, {
    encoding: "utf-8",
    cwd,
    env: process.env,
    stdio: "inherit",
  });
}

export function installChainlit() {
  runCommand("npm run build", FRONTEND_DIR);
  runCommand("pip3 install -e ./src");
}

export function runSpec(test: string) {
  // Recording the cypress run is time consuming. Disabled by default.
  // const recordOptions = ` --record --key ${process.env.CYPRESS_RECORD_KEY} `;
  return runCommand(
    `npx cypress run --record false --spec cypress/e2e/${test}/spec.cy.ts`
  );
}

export async function runChainlit(dir: string, file: string, localDb = false) {
  return new Promise((resolve, reject) => {
    const options = ["run", file];

    if (localDb) {
      options.push("--db");
      options.push("local");
    }

    const server = spawn("chainlit", options, {
      cwd: dir,
    });

    server.stdout.on("data", (data) => {
      console.log(`stdout: ${data}`);
      if (data.toString().includes("Your app is available at")) {
        resolve(server);
      }
    });

    server.stderr.on("data", (data) => {
      console.error(`stderr: ${data}`);
    });

    server.on("error", (error) => {
      reject(error.message);
    });

    server.on("exit", function (code) {
      reject("child process exited with code " + code);
    });
  });
}
