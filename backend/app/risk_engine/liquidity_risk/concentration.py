from typing import List, Dict, Any

def calculate_concentration(positions: List[Dict[str, Any]], dimension: str) -> List[Dict[str, Any]]:
    total_mv = sum(float(p['market_value']) for p in positions)
    if total_mv <= 0:
        return []

    groups = {}
    for p in positions:
        val = p.get(dimension, 'Unknown')
        if val is None:
            val = 'Unknown'
        
        if val not in groups:
            groups[val] = {'market_value': 0.0, 'position_count': 0}
        
        groups[val]['market_value'] += float(p['market_value'])
        groups[val]['position_count'] += 1

    results = []
    for val, data in groups.items():
        mv = data['market_value']
        results.append({
            'bucket_name': str(val),
            'market_value': mv,
            'portfolio_weight': mv / total_mv,
            'position_count': data['position_count']
        })
    
    results.sort(key=lambda x: x['market_value'], reverse=True)
    return results

def calculate_hhi(concentration_results: List[Dict[str, Any]]) -> float:
    return sum(r['portfolio_weight'] ** 2 for r in concentration_results)
