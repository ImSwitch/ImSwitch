from imswitch.imcommon.model import APIExport, initLogger

from ..basecontrollers import ImConWidgetController, SetupModeMixin


class FlipMirrorController(SetupModeMixin, ImConWidgetController):
    """Controller for FlipMirrorWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__logger = initLogger(self, tryInheritParent=True)

        self._manager = getattr(self._master, "flipMirrorsManager", None)
        self._names = []

        # follower -> master
        self._master_by_follower = {}

        # master -> set(followers)
        self._followers_by_master = {}

        if self._manager is None or not self._manager.hasDevices():
            self._widget.setAllEnabled(False)
            return

        self._names = self._manager.getAllDeviceNames()

        for name in self._names:
            manager = self._manager[name]

            if hasattr(manager, "get_state_names"):
                state_names = manager.get_state_names()
            else:
                state_names = {0: "0", 1: "1"}

            self._widget.addFlipMirror(name, state_names=state_names)

        self._widget.sigStateChanged.connect(self.move_flip)
        self._widget.sigLinkChanged.connect(self.set_link)
        self._widget.sigResetConnectionsClicked.connect(self.reset_connections)

        self._refresh_all_states()
        self._refresh_link_ui()

    def closeEvent(self):
        pass

    def getSetupModeState(self):
        mirrors = {}

        for name in self._names:
            state = None
            connected = self._is_connected(name)
            if connected:
                try:
                    state = int(self._manager[name].get_state())
                except Exception as e:
                    self.__logger.error(f"Failed to snapshot flip mirror {name}: {e}")

            mirrors[name] = {
                "state": state,
                "connected": connected,
            }

        return {
            "mirrors": mirrors,
            "links": dict(self._master_by_follower),
        }

    def applySetupModeState(self, state):
        warnings = []

        if self._manager is None or not self._manager.hasDevices():
            return ["No flip mirror manager/devices are available."]

        if not isinstance(state, dict):
            return ["Saved flip mirror state is not a dictionary."]

        mirrors = state.get("mirrors", {})
        links = state.get("links", {})

        if not isinstance(mirrors, dict):
            warnings.append("Saved flip mirror mirror-state section is not a dictionary.")
            mirrors = {}
        if not isinstance(links, dict):
            warnings.append("Saved flip mirror link section is not a dictionary.")
            links = {}

        # Remove existing links first so physical states can be restored without
        # follower propagation from the old link graph.
        for follower in list(self._master_by_follower.keys()):
            self.set_link(follower, None)

        for name, mirrorState in mirrors.items():
            if name not in self._names:
                warnings.append(f'Flip mirror "{name}" is not available.')
                continue

            if not self._is_connected(name):
                warnings.append(f'Flip mirror "{name}" is not connected.')
                continue

            if isinstance(mirrorState, dict):
                savedState = mirrorState.get("state")
            else:
                savedState = mirrorState

            if savedState is None:
                warnings.append(f'Flip mirror "{name}" has no saved state.')
                continue

            if not self._safe_move_one(name, int(savedState)):
                warnings.append(f'Failed to move flip mirror "{name}" to state {savedState}.')

        for follower, master in links.items():
            if follower not in self._names:
                warnings.append(f'Flip mirror follower "{follower}" is not available.')
                continue
            if master not in self._names:
                warnings.append(f'Flip mirror master "{master}" is not available.')
                continue
            if not self.set_link(follower, master):
                warnings.append(f'Failed to restore flip mirror link {follower} -> {master}.')

        self._refresh_link_ui()
        return warnings

    def _is_connected(self, name):
        try:
            return bool(self._manager[name].is_connected())
        except Exception:
            return False

    def _get_error(self, name):
        try:
            return self._manager[name].get_last_error()
        except Exception:
            return None

    def _safe_get_state(self, name):
        try:
            state = self._manager[name].get_state()
            self._widget.setState(name, state)
            return state
        except Exception as e:
            self.__logger.error(f"Failed to read flip mirror {name}: {e}")
            return None

    def _safe_move_one(self, name, state):
        try:
            self._manager[name].move_to(state)
            self._widget.setState(name, state)
            return True
        except Exception as e:
            self.__logger.error(f"Failed to move flip mirror {name} to {state}: {e}")
            return False

    def _refresh_all_states(self):
        for name in self._names:
            if self._is_connected(name):
                self._safe_get_state(name)

        self._refresh_link_ui()

    def _refresh_link_ui(self):
        for name in self._names:
            current_master = self._master_by_follower.get(name)

            choices = self._valid_master_choices_for(name)
            self._widget.setMasterChoices(name, choices, current_master=current_master)
            self._widget.setLink(name, current_master)

        for name in self._names:
            connected = self._is_connected(name)
            is_follower = name in self._master_by_follower
            has_followers = len(self._followers_by_master.get(name, set())) > 0

            state_enabled = connected and not is_follower

            # A follower must keep link controls enabled so it can be unlinked.
            # A master with followers cannot itself be linked to something else.
            link_enabled = connected and not has_followers

            if not connected:
                error = self._get_error(name)
                status = "Error" if error else "Disconnected"
            else:
                status = "OK"

            self._widget.setRowState(
                name,
                connected=connected,
                state_enabled=state_enabled,
                link_enabled=link_enabled,
                status_text=status,
            )

    def _valid_master_choices_for(self, follower_name):
        choices = []

        for candidate in self._names:
            if candidate == follower_name:
                continue

            if not self._is_connected(candidate):
                continue

            # No chains: a follower cannot be used as a master.
            if candidate in self._master_by_follower:
                continue

            # A mirror that already follows something cannot itself become a follower.
            # If follower_name has followers, it should not be linkable.
            if len(self._followers_by_master.get(follower_name, set())) > 0:
                continue

            choices.append(candidate)

        return choices

    def _is_valid_link(self, follower_name, master_name):
        if follower_name not in self._names:
            return False

        if master_name not in self._names:
            return False

        if follower_name == master_name:
            return False

        if not self._is_connected(follower_name) or not self._is_connected(master_name):
            return False

        # No chains: master cannot already be a follower.
        if master_name in self._master_by_follower:
            return False

        # No chains/cycles: follower cannot already be a master.
        if len(self._followers_by_master.get(follower_name, set())) > 0:
            return False

        return True

    @APIExport(runOnUIThread=True)
    def move_flip(self, name, state):
        """Move one flip mirror and all linked followers to state 0 or 1."""
        state = int(state)

        if name in self._master_by_follower:
            self.__logger.warning(f"Ignoring manual move for follower flip mirror {name}")
            self._refresh_link_ui()
            return

        if name not in self._names:
            self.__logger.error(f"Unknown flip mirror: {name}")
            return

        ok = self._safe_move_one(name, state)

        for follower in sorted(self._followers_by_master.get(name, set())):
            follower_ok = self._safe_move_one(follower, state)
            ok = ok and follower_ok

        self._refresh_link_ui()
        return ok

    @APIExport(runOnUIThread=True)
    def set_link(self, follower_name, master_name):
        """Set or remove follower -> master link."""
        if follower_name not in self._names:
            self.__logger.error(f"Unknown follower flip mirror: {follower_name}")
            return False

        # Unlink
        if master_name is None:
            old_master = self._master_by_follower.pop(follower_name, None)
            if old_master is not None:
                self._followers_by_master.get(old_master, set()).discard(follower_name)
                if len(self._followers_by_master.get(old_master, set())) == 0:
                    self._followers_by_master.pop(old_master, None)

            self._refresh_link_ui()
            return True

        # Link
        if not self._is_valid_link(follower_name, master_name):
            self.__logger.error(
                f"Invalid flip mirror link: {follower_name} -> {master_name}"
            )
            self._refresh_link_ui()
            return False

        # Remove previous link if any.
        old_master = self._master_by_follower.pop(follower_name, None)
        if old_master is not None:
            self._followers_by_master.get(old_master, set()).discard(follower_name)

        self._master_by_follower[follower_name] = master_name
        self._followers_by_master.setdefault(master_name, set()).add(follower_name)

        # Immediate sync: follower physically takes master's current state.
        master_state = self._safe_get_state(master_name)
        if master_state is not None:
            self._safe_move_one(follower_name, master_state)

        self._refresh_link_ui()
        return True

    @APIExport(runOnUIThread=True)
    def reset_connections(self):
        """Close/reopen all flip mirror connections and re-sync followers."""
        if self._manager is None:
            return False

        try:
            self._manager.reset_connections()
        except Exception as e:
            self.__logger.error(f"Failed to reset flip mirror connections: {e}")

        self._refresh_all_states()

        # Re-sync followers after reconnection.
        for follower, master in list(self._master_by_follower.items()):
            if not self._is_connected(follower) or not self._is_connected(master):
                continue

            master_state = self._safe_get_state(master)
            if master_state is not None:
                self._safe_move_one(follower, master_state)

        self._refresh_link_ui()
        return True

    @APIExport(runOnUIThread=True)
    def get_flip_state(self, name):
        """Return current state of one flip mirror."""
        if name not in self._names:
            raise ValueError(f"Unknown flip mirror: {name}")

        return self._manager[name].get_state()
