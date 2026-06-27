# bash completion for mys
# Install: copy to ~/.local/share/bash-completion/completions/mys
#   mkdir -p ~/.local/share/bash-completion/completions
#   cp completions/mys.bash ~/.local/share/bash-completion/completions/mys
# Or source directly: source /path/to/completions/mys.bash

_mys() {
    local cur prev words cword
    _init_completion || return

    # ── helpers ───────────────────────────────────────────────────────────────

    # Resolve the registry path in effect for this command line.
    # Priority: --registry-path flag in COMP_WORDS > MYS_REGISTRY_PATH > XDG default.
    _mys_registry_path() {
        local i
        for (( i = 1; i < ${#words[@]} - 1; i++ )); do
            if [[ "${words[i]}" == "--registry-path" ]]; then
                printf '%s' "${words[i+1]}"
                return
            fi
        done
        if [[ -n "${MYS_REGISTRY_PATH:-}" ]]; then
            printf '%s' "${MYS_REGISTRY_PATH}"
            return
        fi
        printf '%s' "${HOME}/.local/share/mys/registry.tsv"
    }

    # Return installed command names from column 1 of the registry TSV.
    _mys_installed_commands() {
        local registry
        registry="$(_mys_registry_path)"
        registry="${registry/#\~/$HOME}"
        [[ -f "$registry" ]] || return
        awk -F'\t' 'NF==5 { print $1 }' "$registry" 2>/dev/null
    }

    # ── constants ─────────────────────────────────────────────────────────────

    local -r COMMANDS='install update remove list export import sync url config self-update'
    local -r GLOBAL_FLAGS='--repo --branch --bin-dir --registry-path --config-path'
    local -r FLAGS_INSTALL='--as --keep-extension'
    local -r FLAGS_UPDATE='--as --keep-extension'
    local -r FLAGS_IMPORT='--replace'
    local -r FLAGS_CONFIG='--repo --branch --bin-dir --registry-path'

    # ── detect current command ────────────────────────────────────────────────

    local cmd=''
    local i
    for (( i = 1; i < cword; i++ )); do
        case "${words[i]}" in
            --repo|--branch|--bin-dir|--registry-path|--config-path|--as)
                (( i++ ))
                ;;
            --keep-extension|--replace)
                ;;
            -*)
                ;;
            *)
                if [[ -z "$cmd" ]]; then
                    cmd="${words[i]}"
                fi
                ;;
        esac
    done

    # ── no command yet — offer commands and global flags ──────────────────────

    if [[ -z "$cmd" ]]; then
        case "$cur" in
            --*)
                COMPREPLY=( $(compgen -W "$GLOBAL_FLAGS" -- "$cur") )
                return
                ;;
        esac
        COMPREPLY=( $(compgen -W "$COMMANDS $GLOBAL_FLAGS" -- "$cur") )
        return
    fi

    # ── flag completion for current command ───────────────────────────────────

    if [[ "$cur" == --* ]]; then
        case "$cmd" in
            install)   COMPREPLY=( $(compgen -W "$FLAGS_INSTALL $GLOBAL_FLAGS" -- "$cur") ) ;;
            update)    COMPREPLY=( $(compgen -W "$FLAGS_UPDATE  $GLOBAL_FLAGS" -- "$cur") ) ;;
            import)    COMPREPLY=( $(compgen -W "$FLAGS_IMPORT  $GLOBAL_FLAGS" -- "$cur") ) ;;
            config)    COMPREPLY=( $(compgen -W "$FLAGS_CONFIG  $GLOBAL_FLAGS" -- "$cur") ) ;;
            *)         COMPREPLY=( $(compgen -W "$GLOBAL_FLAGS" -- "$cur") ) ;;
        esac
        return
    fi

    # ── value completion for flags that take arguments ────────────────────────

    case "$prev" in
        --bin-dir)
            _filedir -d
            return
            ;;
        --registry-path|--config-path)
            _filedir
            return
            ;;
        --repo|--branch|--as)
            return
            ;;
    esac

    # ── positional completion by command ──────────────────────────────────────

    case "$cmd" in

        install|update|url)
            # Complete local .py/.sh/.mjs files and directories.
            local IFS=$'\n'
            local -a matches filtered=()
            mapfile -t matches < <(compgen -f -- "$cur")
            local f
            for f in "${matches[@]}"; do
                case "$f" in
                    *.py|*.sh|*.mjs) filtered+=( "$f" ) ;;
                    *) [[ -d "$f" ]] && filtered+=( "$f" ) ;;
                esac
            done
            COMPREPLY=( "${filtered[@]}" )
            [[ ${#COMPREPLY[@]} -eq 1 && -d "${COMPREPLY[0]}" ]] && COMPREPLY[0]+='/'
            compopt -o nospace 2>/dev/null
            return
            ;;

        remove)
            local -a installed
            mapfile -t installed < <(_mys_installed_commands)
            COMPREPLY=( $(compgen -W "${installed[*]}" -- "$cur") )
            return
            ;;

        export)
            _filedir
            return
            ;;

        import)
            local IFS=$'\n'
            local -a all tsv_files=()
            mapfile -t all < <(compgen -f -- "$cur")
            local f
            for f in "${all[@]}"; do
                [[ "$f" == *.tsv || -d "$f" ]] && tsv_files+=( "$f" )
            done
            COMPREPLY=( "${tsv_files[@]}" )
            [[ ${#COMPREPLY[@]} -eq 1 && -d "${COMPREPLY[0]}" ]] && COMPREPLY[0]+='/'
            compopt -o nospace 2>/dev/null
            return
            ;;

        list|sync|self-update|config)
            return
            ;;

    esac
}

complete -F _mys mys
