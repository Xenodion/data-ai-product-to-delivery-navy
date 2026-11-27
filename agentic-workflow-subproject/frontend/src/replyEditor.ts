export type ReplyEditorState = { text: string; base: string; conflict: boolean };

/** Keep local edits when a newer server reply arrives; never silently overwrite them. */
export function reconcileReply(state: ReplyEditorState, reply: string): ReplyEditorState {
  if (reply === state.base) return state;
  if (state.text === state.base || state.text === reply) return { text: reply, base: reply, conflict: false };
  return { ...state, base: reply, conflict: true };
}
