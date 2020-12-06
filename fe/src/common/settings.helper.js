export const SettingsHelper = {
    getShowProxyTo() {
        return localStorage.showProxyTo ? localStorage.showProxyTo : defaultClientSettings.showProxyTo;
    }
}

const defaultClientSettings = {
    showProxyTo: true,
    candidatesSorting: CANDIDATES_SORTING_NEAREST
}

export const CANDIDATES_SORTING_NEAREST = 'nearest'
export const CANDIDATES_SORTING_SIMILAR = 'similar'