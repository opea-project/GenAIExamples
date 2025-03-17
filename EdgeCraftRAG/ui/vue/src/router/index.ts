
import { createRouter, createWebHashHistory } from 'vue-router';
import { routeList, notFoundAndNoPower } from './routes';

const router = createRouter({
	history: createWebHashHistory(),
  routes: [...notFoundAndNoPower, ...routeList],
});

export default router;