jest.mock("child_process", () => ({
    execSync: jest.fn()
}));

const { execSync } = require("child_process");

const {
    toModule,
    runExample,
    runAll,
    computeExecutionPlan
} = require("../pr-check-secondary-examples");

describe("toModule", () => {
    test("converts file path to module", () => {
        expect(toModule("examples/a/b.py")).toBe("examples.a.b");
    });
});

describe("computeExecutionPlan", () => {
    test("removes changed files from remaining", () => {
        const all = ["examples/a.py", "examples/b.py"];
        const changed = ["examples/b.py"];

        const { remaining } = computeExecutionPlan(all, changed);

        expect(remaining).toEqual(["examples/a.py"]);
    });
});

describe("runExample", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("runs successfully", () => {
        execSync.mockImplementation(() => { });

        expect(() => runExample("examples/a.py")).not.toThrow();

        expect(execSync).toHaveBeenCalledWith(
            "uv run -m examples.a",
            expect.objectContaining({ stdio: "inherit" })
        );
    });

    test("fails and exits", () => {
        execSync.mockImplementation(() => {
            throw new Error("fail");
        });

        const exitSpy = jest
            .spyOn(process, "exit")
            .mockImplementation(() => { throw new Error("exit"); });

        expect(() => runExample("examples/a.py")).toThrow("exit");

        expect(exitSpy).toHaveBeenCalledWith(1);

        exitSpy.mockRestore();
    });
});
describe("runAll", () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    test("runs all files", () => {
        execSync.mockImplementation(() => { });

        runAll(["examples/a.py", "examples/b.py"]);

        expect(execSync).toHaveBeenCalledTimes(2);
    });

    test("stops on first failure", () => {
        execSync
            .mockImplementationOnce(() => { })
            .mockImplementationOnce(() => {
                throw new Error("fail");
            });

        const exitSpy = jest
            .spyOn(process, "exit")
            .mockImplementation(() => { throw new Error("exit"); });

        expect(() =>
            runAll(["examples/a.py", "examples/b.py"])
        ).toThrow("exit");

        expect(exitSpy).toHaveBeenCalledWith(1);

        exitSpy.mockRestore();
    });
});