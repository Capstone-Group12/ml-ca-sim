import { z } from "zod";

export const AttackType = z.enum([
  "DDOS",
  "XSS_SQL_INJECTION",
  "SLOWLORIS",
  "BRUTE_FORCE",
  "DNS_POISONING"
]);

export const MLModel = z.enum([
  "LSTM",
  "RANDOM_FOREST",
  "NAIVE_BAYES",
  "LOGISTIC_REGRESSION",
  "DECISION_TREE",
  "ISOLATION_FOREST",
  "GRADIENT_BOOSTING",
  "SMALL_NN"
]);

export const AttackSchema = z.object({
  name: AttackType,
  mlModels: z.array(MLModel).nonempty()
});

export const AttackListSchema = z.array(AttackSchema);

// TS types (optional but helpful)
export type Attack = z.infer<typeof AttackSchema>;
export type AttackList = z.infer<typeof AttackListSchema>;
