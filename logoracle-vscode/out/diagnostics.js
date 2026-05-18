"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.DiagnosticsManager = void 0;
// src/diagnostics.ts
const vscode = __importStar(require("vscode"));
const SEV_MAP = {
    CRITICAL: vscode.DiagnosticSeverity.Error,
    HIGH: vscode.DiagnosticSeverity.Error,
    MEDIUM: vscode.DiagnosticSeverity.Warning,
    LOW: vscode.DiagnosticSeverity.Information,
    INFO: vscode.DiagnosticSeverity.Hint,
};
class DiagnosticsManager {
    constructor(ctx) {
        this.collection = vscode.languages.createDiagnosticCollection("logoracle");
        ctx.subscriptions.push(this.collection);
    }
    applyIssues(doc, issues) {
        const diags = issues
            .filter(issue => issue.line != null)
            .map(issue => {
            const line = Math.max(0, (issue.line || 1) - 1);
            const lineText = doc.lineAt(Math.min(line, doc.lineCount - 1));
            const range = new vscode.Range(line, lineText.firstNonWhitespaceCharacterIndex, line, lineText.text.length);
            const diag = new vscode.Diagnostic(range, `[LogOracle] ${issue.message}${issue.cwe_id ? ` (${issue.cwe_id})` : ""}`, SEV_MAP[issue.severity] ?? vscode.DiagnosticSeverity.Warning);
            diag.source = "LogOracle";
            diag.code = issue.rule_id || issue.cwe_id || "LO001";
            return diag;
        });
        this.collection.set(doc.uri, diags);
    }
    clear(doc) {
        if (doc)
            this.collection.delete(doc.uri);
        else
            this.collection.clear();
    }
}
exports.DiagnosticsManager = DiagnosticsManager;
//# sourceMappingURL=diagnostics.js.map