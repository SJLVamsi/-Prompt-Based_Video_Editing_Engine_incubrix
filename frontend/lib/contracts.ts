import { z } from "zod";
export const EditOp = z.discriminatedUnion("op", [
  z.object({ op: z.literal("cut"), start: z.number(), end: z.number() }),
  z.object({ op: z.literal("keep"), start: z.number(), end: z.number() }),
  z.object({ op: z.literal("speed"), start: z.number(), end: z.number(), factor: z.number().min(0.25).max(4) }),
  z.object({ op: z.literal("caption"), start: z.number(), end: z.number(), text: z.string().min(1), style: z.enum(["hook","subtitle","cta"]).optional() }),
]);
export const EditPlan = z.object({ version: z.literal("v1"), ops: z.array(EditOp).max(50), response: z.enum(["results","clarify","reject"]).default("results") });
export type TimelineClip = { id: string; start: number; end: number };
