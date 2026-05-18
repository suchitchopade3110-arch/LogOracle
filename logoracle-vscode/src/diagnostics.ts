// src/diagnostics.ts
import * as vscode from "vscode";

const SEV_MAP: Record<string, vscode.DiagnosticSeverity> = {
    CRITICAL: vscode.DiagnosticSeverity.Error,
    HIGH:     vscode.DiagnosticSeverity.Error,
    MEDIUM:   vscode.DiagnosticSeverity.Warning,
    LOW:      vscode.DiagnosticSeverity.Information,
    INFO:     vscode.DiagnosticSeverity.Hint,
};

export class DiagnosticsManager {
    private collection: vscode.DiagnosticCollection;

    constructor(ctx: vscode.ExtensionContext) {
        this.collection = vscode.languages.createDiagnosticCollection("logoracle");
        ctx.subscriptions.push(this.collection);
    }

    applyIssues(doc: vscode.TextDocument, issues: any[]) {
        const diags: vscode.Diagnostic[] = issues
            .filter(issue => issue.line != null)
            .map(issue => {
                const line     = Math.max(0, (issue.line || 1) - 1);
                const lineText = doc.lineAt(Math.min(line, doc.lineCount - 1));
                const range    = new vscode.Range(
                    line, lineText.firstNonWhitespaceCharacterIndex,
                    line, lineText.text.length
                );

                const diag = new vscode.Diagnostic(
                    range,
                    `[LogOracle] ${issue.message}${issue.cwe_id ? ` (${issue.cwe_id})` : ""}`,
                    SEV_MAP[issue.severity] ?? vscode.DiagnosticSeverity.Warning
                );
                diag.source = "LogOracle";
                diag.code   = issue.rule_id || issue.cwe_id || "LO001";
                return diag;
            });

        this.collection.set(doc.uri, diags);
    }

    clear(doc?: vscode.TextDocument) {
        if (doc) this.collection.delete(doc.uri);
        else     this.collection.clear();
    }
}
