"use client";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Trophy, Clock, CheckCircle, XCircle, Zap } from "lucide-react";
import { useStore } from "@/store";
import {
  checkStreak,
  generateQuiz,
  getBadgeEvents,
  getLeaderboard,
  scheduleQuiz,
  submitQuizAnswer,
  updateLeaderboard,
} from "@/lib/api";

export default function QuizPage() {
  const { xp, addXP, findings, leaderboard, setLeaderboard } = useStore();
  const [quiz, setQuiz] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<any>(null);
  const [timer, setTimer] = useState(0);
  const [badgeToast, setBadgeToast] = useState<any>(null);
  const timerRef = useRef<any>(null);
  const badgeSince = useRef(0);

  useEffect(() => {
    const refreshLeaderboard = () => getLeaderboard()
      .then((r) => setLeaderboard(r.leaderboard || []))
      .catch(() => {});
    const pollBadges = () => getBadgeEvents(badgeSince.current)
      .then((r) => {
        badgeSince.current = r.timestamp || Date.now() / 1000;
        if (r.events?.length) setBadgeToast(r.events[r.events.length - 1]);
      })
      .catch(() => {});

    refreshLeaderboard();
    pollBadges();
    const lb = setInterval(refreshLeaderboard, 60000);
    const badges = setInterval(pollBadges, 10000);
    return () => { clearInterval(lb); clearInterval(badges); };
  }, [setLeaderboard]);

  const startTimer = () => {
    setTimer(0);
    timerRef.current = setInterval(() => setTimer((t) => t + 1), 1000);
  };
  const stopTimer = () => clearInterval(timerRef.current);

  const loadQuiz = async () => {
    setLoading(true); setSelected(null); setResult(null);
    const bug = findings[0]?.message || "SQL injection vulnerability in user input";
    try {
      const q = await generateQuiz(bug, "python");
      setQuiz(q);
      startTimer();
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (idx: number) => {
    if (selected !== null || !quiz) return;
    setSelected(idx);
    stopTimer();
    const res = await submitQuizAnswer(quiz.question_id || "q1", idx, timer);
    setResult(res);
    const correct = !!res.correct;
    await scheduleQuiz("local-dev", quiz.question_id || "q1", correct, timer).catch(() => {});
    if (correct) await checkStreak("local-dev", "Local Developer").catch(() => {});
    if (res.xp_awarded) {
      addXP(res.xp_awarded);
      await updateLeaderboard("local-dev", "Local Developer", res.xp_awarded, correct ? "correct_quiz" : "quiz_attempt").catch(() => {});
      const lb = await getLeaderboard().catch(() => null);
      if (lb?.leaderboard) setLeaderboard(lb.leaderboard);
    }
  };

  return (
    <div className="flex flex-col h-full p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Trophy size={20} className="text-oracle-accent" />
        <h1 className="font-display font-bold text-xl text-oracle-text">Developer Growth</h1>
        <div className="ml-auto flex items-center gap-2 bg-oracle-surface border border-oracle-border
                        rounded-full px-3 py-1">
          <Zap size={12} className="text-oracle-accent" />
          <span className="text-sm font-mono text-oracle-accent">{xp.total} XP</span>
        </div>
      </div>

      {/* Badges */}
      <AnimatePresence>
        {badgeToast && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mb-4 rounded-xl border border-oracle-accent/30 bg-oracle-accent/10 p-3 text-oracle-accent"
          >
            {badgeToast.icon} Badge unlocked: {badgeToast.badge}
          </motion.div>
        )}
      </AnimatePresence>

      {xp.badges.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {xp.badges.map((b) => (
            <span key={b} className="text-xs px-2 py-1 rounded-full bg-oracle-accent/10
                                     border border-oracle-accent/20 text-oracle-accent font-mono">
              {b}
            </span>
          ))}
        </div>
      )}

      {leaderboard.length > 0 && (
        <div className="mb-5 rounded-xl border border-oracle-border bg-oracle-surface overflow-hidden">
          <div className="px-3 py-2 border-b border-oracle-border text-xs text-oracle-subtext font-mono">Leaderboard</div>
          {leaderboard.slice(0, 5).map((row: any, i) => (
            <div key={row.developer_id || i} className="flex items-center px-3 py-2 text-xs border-b border-oracle-border last:border-0">
              <span className="text-oracle-subtext w-6">#{i + 1}</span>
              <span className="text-oracle-text">{row.name}</span>
              <span className="ml-auto text-oracle-accent font-mono">{row.xp_total} XP</span>
            </div>
          ))}
        </div>
      )}

      {/* Quiz card */}
      <AnimatePresence mode="wait">
        {!quiz ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex-1 flex flex-col items-center justify-center"
          >
            <Trophy size={48} className="text-oracle-subtext mb-4 opacity-20" />
            <p className="text-oracle-subtext text-sm mb-6">
              {findings.length > 0
                ? `Generate a quiz from the current ${findings[0].severity} finding`
                : "Analyze logs first to generate context-aware quizzes"}
            </p>
            <button
              onClick={loadQuiz}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 rounded-xl font-mono text-sm
                         bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent
                         hover:bg-oracle-accent/20 transition-colors disabled:opacity-30"
            >
              {loading
                ? <span className="w-4 h-4 border border-oracle-accent/50 border-t-oracle-accent rounded-full animate-spin" />
                : <Trophy size={16} />}
              {loading ? "Generating..." : "Generate Quiz"}
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="quiz"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex-1 flex flex-col"
          >
            {/* Timer */}
            <div className="flex items-center gap-2 mb-4 text-oracle-subtext">
              <Clock size={13} />
              <span className="font-mono text-sm">{timer}s</span>
              {result?.time_bonus && (
                <span className="text-oracle-success text-xs ml-2">+{result.time_bonus} time bonus!</span>
              )}
            </div>

            {/* Question */}
            <div className="bg-oracle-surface border border-oracle-border rounded-xl p-4 mb-4">
              <p className="text-sm font-mono text-oracle-subtext mb-2 uppercase tracking-wider">Question</p>
              <p className="text-oracle-text leading-relaxed">{quiz.question}</p>
            </div>

            {/* Options */}
            <div className="space-y-2 mb-6">
              {quiz.options?.map((opt: string, i: number) => {
                const isSelected = selected === i;
                const isCorrect = result && i === result.correct_index;
                const isWrong = isSelected && result && !result.correct;

                return (
                  <motion.button
                    key={i}
                    onClick={() => submitAnswer(i)}
                    disabled={selected !== null}
                    whileHover={selected === null ? { x: 4 } : {}}
                    className={`w-full text-left p-3 rounded-lg border text-sm transition-all
                      ${isCorrect ? "border-oracle-success bg-oracle-success/10 text-oracle-success" :
                        isWrong ? "border-oracle-danger bg-oracle-danger/10 text-oracle-danger" :
                        isSelected ? "border-oracle-accent bg-oracle-accent/10 text-oracle-accent" :
                        "border-oracle-border hover:border-oracle-accent/40 text-oracle-text"
                      } ${selected !== null ? "cursor-default" : "cursor-pointer"}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs opacity-50">{String.fromCharCode(65 + i)}</span>
                      <span>{opt}</span>
                      {isCorrect && <CheckCircle size={14} className="ml-auto" />}
                      {isWrong && <XCircle size={14} className="ml-auto" />}
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {/* Result */}
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-xl border mb-4 ${
                  result.correct
                    ? "border-oracle-success/40 bg-oracle-success/5"
                    : "border-oracle-danger/40 bg-oracle-danger/5"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {result.correct
                    ? <><CheckCircle size={14} className="text-oracle-success" /><span className="text-oracle-success font-mono text-sm">Correct!</span></>
                    : <><XCircle size={14} className="text-oracle-danger" /><span className="text-oracle-danger font-mono text-sm">Incorrect</span></>
                  }
                  {result.xp_awarded > 0 && (
                    <span className="ml-auto text-oracle-accent font-mono text-sm">+{result.xp_awarded} XP</span>
                  )}
                </div>
                {result.explanation && <p className="text-xs text-oracle-subtext leading-relaxed">{result.explanation}</p>}
              </motion.div>
            )}

            {result && (
              <button
                onClick={loadQuiz}
                className="self-start flex items-center gap-2 px-4 py-2 rounded-lg font-mono text-sm
                           bg-oracle-accent/10 border border-oracle-accent/30 text-oracle-accent
                           hover:bg-oracle-accent/20 transition-colors"
              >
                Next Question →
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
