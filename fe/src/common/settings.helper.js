export const SettingsHelper = {
    getShowProxyTo() {
        return localStorage.showProxyTo ? localStorage.showProxyTo : defaultClientSettings.showProxyTo;
    },
    getHideMarkedTo() {
        return localStorage.hideMarkedTo ? localStorage.hideMarkedTo : defaultClientSettings.hideMarkedTo;
    },
    getHideMarkedFrom() {
        return localStorage.hideMarkedFrom ? localStorage.hideMarkedFrom : defaultClientSettings.hideMarkedFrom;
    },
}

const defaultClientSettings = {
    showProxyTo: true,
    hideMarkedTo: false,
    hideMarkedFrom: false,
    candidatesSorting: CANDIDATES_SORTING_NEAREST
}

export const CANDIDATES_SORTING_NEAREST = 'nearest'
export const CANDIDATES_SORTING_SIMILAR = 'similar'
