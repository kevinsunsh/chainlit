import { atom } from 'recoil';

export interface IPlaygroundState {
  prompt: string;
  completion: string;
}

export const playgroundState = atom<IPlaygroundState | undefined>({
  key: 'Playground',
  default: undefined
});
