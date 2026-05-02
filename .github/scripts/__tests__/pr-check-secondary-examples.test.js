jest.mock("child_process", () => ({
    execSync: jest.fn(),
    spawnSync: jest.fn(),
}));

const { execSync, spawnSync } = require("child_process");

const {
    toModule,
    getAllExamples,
    getChangedExamples,
    runExample,
    runAll,
    computeExecutionPlan,
} = require("../pr-check-secondary-examples");

// ---------------------------------------------------------------------------
// toModule
// ---------------------------------------------------------------------------
describe("toModule", () => {
    test("converts nested path to module", () => {
        expect(toModule("examples/a/b.py")).toBe("examples.a.b");
    });

    test("converts root-level example path to module", () => {
        expect(toModule("examples/foo.py")).toBe("examples.foo");
    });
});

// ---------------------------------------------------------------------------
// getAllExamples
// ---------------------------------------------------------------------------
describe("getAllExamples", () => {
    beforeEach(() => jest.clearAllMocks());

    test("returns list of example files", () => {
        execSync.mockReturnValueOnce("examples/a.py\nexamples/b/c.py\n");

        expect(getAllExamples()).toEqual(["examples/a.py", "examples/b/c.py"]);
    });

    test("excludes __init__.py files", () => {
        execSync.mockReturnValueOnce("examples/a.py\nexamples/__init__.py\nexamples/b.py\n");

        expect(getAllExamples()).toEqual(["examples/a.py", "examples/b.py"]);
    });

    test("returns empty array when git ls-files produces no output", () => {
        execSync.mockReturnValueOnce("");

        expect(getAllExamples()).toEqual([]);
    });
});

// ---------------------------------------------------------------------------
// getChangedExamples
// ---------------------------------------------------------------------------
describe("getChangedExamples", () => {
    const ORIG_ENV = process.env;

    beforeEach(() => {
        jest.clearAllMocks();
        process.env = { ...ORIG_ENV };
    });

    afterEach(() => {
        process.env = ORIG_ENV;
    });

    test("returns empty array when GITHUB_BASE_REF is not set", () => {
        delete process.env.GITHUB_BASE_REF;

        expect(getChangedExamples()).toEqual([]);
        expect(execSync).not.toHaveBeenCalled();
    });

    test("returns only changed example .py files", () => {
        process.env.GITHUB_BASE_REF = "main";
        execSync
            .mockReturnValueOnce("") // git fetch
            .mockReturnValueOnce("examples/a.py\nsrc/foo.py\nexamples/b.py\nREADME.md\n");

        expect(getChangedExamples()).toEqual(["examples/a.py", "examples/b.py"]);
    });

    test("filters out non-.py files under examples/", () => {
        process.env.GITHUB_BASE_REF = "main";
        execSync
            .mockReturnValueOnce("")
            .mockReturnValueOnce("examples/a.py\nexamples/data.json\nexamples/b.py\n");

        expect(getChangedExamples()).toEqual(["examples/a.py", "examples/b.py"]);
    });

    test("returns empty array when diff is empty", () => {
        process.env.GITHUB_BASE_REF = "main";
        execSync
            .mockReturnValueOnce("")
            .mockReturnValueOnce("");

        expect(getChangedExamples()).toEqual([]);
    });

    test("returns empty array when execSync throws", () => {
        process.env.GITHUB_BASE_REF = "main";
        execSync.mockImplementationOnce(() => { throw new Error("git failed"); });

        expect(getChangedExamples()).toEqual([]);
    });
});

// ---------------------------------------------------------------------------
// computeExecutionPlan
// ---------------------------------------------------------------------------
describe("computeExecutionPlan", () => {
    test("removes changed files from remaining", () => {
        const all = ["examples/a.py", "examples/b.py"];
        const changed = ["examples/b.py"];

        const { remaining } = computeExecutionPlan(all, changed);

        expect(remaining).toEqual(["examples/a.py"]);
    });

    test("remaining is all files when nothing changed", () => {
        const all = ["examples/a.py", "examples/b.py"];

        const { remaining } = computeExecutionPlan(all, []);

        expect(remaining).toEqual(all);
    });

    test("remaining is empty when all files changed", () => {
        const all = ["examples/a.py", "examples/b.py"];

        const { remaining } = computeExecutionPlan(all, all);

        expect(remaining).toEqual([]);
    });
});

// ---------------------------------------------------------------------------
// runExample
// ---------------------------------------------------------------------------
describe("runExample", () => {
    beforeEach(() => jest.clearAllMocks());

    test("runs successfully", () => {
        spawnSync.mockReturnValue({ status: 0 });

        expect(() => runExample("examples/a.py")).not.toThrow();

        expect(spawnSync).toHaveBeenCalledWith(
            "uv",
            ["run", "-m", "examples.a"],
            expect.objectContaining({ stdio: "inherit" })
        );
    });

    test("fails and exits with code 1", () => {
        spawnSync.mockReturnValue({ status: 1 });

        const exitSpy = jest
            .spyOn(process, "exit")
            .mockImplementation(() => { throw new Error("exit"); });

        expect(() => runExample("examples/a.py")).toThrow("exit");
        expect(exitSpy).toHaveBeenCalledWith(1);

        exitSpy.mockRestore();
    });
});

// ---------------------------------------------------------------------------
// runAll
// ---------------------------------------------------------------------------
describe("runAll", () => {
    beforeEach(() => jest.clearAllMocks());

    test("runs all files in order", () => {
        spawnSync.mockReturnValue({ status: 0 });

        runAll(["examples/a.py", "examples/b.py"]);

        expect(spawnSync).toHaveBeenCalledTimes(2);
        expect(spawnSync).toHaveBeenNthCalledWith(1, "uv", ["run", "-m", "examples.a"], expect.anything());
        expect(spawnSync).toHaveBeenNthCalledWith(2, "uv", ["run", "-m", "examples.b"], expect.anything());
    });

    test("stops on first failure and does not run subsequent files", () => {
        spawnSync
            .mockReturnValueOnce({ status: 0 })
            .mockReturnValueOnce({ status: 1 });

        const exitSpy = jest
            .spyOn(process, "exit")
            .mockImplementation(() => { throw new Error("exit"); });

        expect(() =>
            runAll(["examples/a.py", "examples/b.py", "examples/c.py"])
        ).toThrow("exit");

        expect(exitSpy).toHaveBeenCalledWith(1);
        expect(spawnSync).toHaveBeenCalledTimes(2);

        exitSpy.mockRestore();
    });

    test("does nothing for empty list", () => {
        runAll([]);

        expect(spawnSync).not.toHaveBeenCalled();
    });
});
