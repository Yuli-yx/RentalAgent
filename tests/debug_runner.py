"""本地调试运行器"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


class DebugRunner:
    """调试运行器，用于本地测试 Agent"""

    def __init__(self, model_ip: str, base_url: str = "http://localhost:8191"):
        self.model_ip = model_ip
        self.base_url = base_url

    async def send_chat(self, session_id: str, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """发送对话请求"""
        url = f"{self.base_url}/api/v1/chat"
        payload = {
            "model_ip": self.model_ip,
            "session_id": session_id,
            "message": message
        }
        if user_id:
            payload["user_id"] = user_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text
                }

    def extract_house_ids(self, response: str) -> List[str]:
        """从响应中提取房源ID列表"""
        house_ids = []

        # 尝试解析 JSON 格式的响应
        try:
            # 尝试直接解析
            data = json.loads(response)
            if isinstance(data, dict) and "houses" in data:
                house_ids = data["houses"]
            elif isinstance(data, list):
                house_ids = data
        except json.JSONDecodeError:
            # 尝试从文本中提取 HF_ 开头的ID
            import re
            matches = re.findall(r'HF_\d+', response)
            house_ids = list(dict.fromkeys(matches))  # 去重保持顺序

        return house_ids

    def load_sample(self, sample_path: str) -> Dict[str, Any]:
        """加载测试样例"""
        with open(sample_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def run_sample(self, sample_path: str) -> Dict[str, Any]:
        """运行单个测试样例"""
        sample = self.load_sample(sample_path)

        print("\n" + "=" * 50)
        print("=== 调试运行 ===")
        print(f"样例: {sample['case_id']}")
        print(f"类型: {sample['case_type']}")
        print(f"描述: {sample['description']}")
        print("=" * 50)

        session_id = f"debug_{sample['case_id']}"
        all_responses = []

        # 按轮次执行对话
        for turn in sample["turns"]:
            print(f"\n--- 第{turn['turn_id']}轮 ---")
            print(f"用户: {turn['message']}")

            result = await self.send_chat(session_id, turn["message"])

            if result.get("error"):
                print(f"错误: {result.get('message')}")
                return {
                    "success": False,
                    "error": result.get("message")
                }

            print(f"Agent: {result['response'][:200]}..." if len(result['response']) > 200 else f"Agent: {result['response']}")
            print(f"耗时: {result['duration_ms']}ms")

            all_responses.append(result['response'])

        # 提取最终结果中的房源ID
        final_response = all_responses[-1]
        actual_houses = self.extract_house_ids(final_response)
        expected_houses = sample.get("expected_houses", [])

        # 计算匹配率
        print("\n" + "=" * 50)
        print("=== 结果对比 ===")
        print(f"预期: {expected_houses}")
        print(f"实际: {actual_houses}")

        if expected_houses:
            matched = set(actual_houses) & set(expected_houses)
            match_rate = len(matched) / len(expected_houses) * 100
            print(f"匹配率: {match_rate:.1f}% ({len(matched)}/{len(expected_houses)})")
        else:
            print("无预期结果，跳过匹配率计算")
            match_rate = None

        return {
            "success": True,
            "case_id": sample["case_id"],
            "expected": expected_houses,
            "actual": actual_houses,
            "match_rate": match_rate,
            "duration_ms": sum([r.get("duration_ms", 0) for r in [result]])
        }

    async def run_all_samples(self, samples_dir: str) -> List[Dict[str, Any]]:
        """运行所有测试样例"""
        results = []
        sample_files = list(Path(samples_dir).glob("*.json"))

        print(f"找到 {len(sample_files)} 个测试样例")

        for sample_file in sorted(sample_files):
            result = await self.run_sample(str(sample_file))
            results.append(result)

        # 输出汇总
        print("\n" + "=" * 50)
        print("=== 汇总报告 ===")
        total = len(results)
        successful = sum(1 for r in results if r.get("success"))
        print(f"总计: {total} 个样例")
        print(f"成功: {successful} 个")
        print(f"失败: {total - successful} 个")

        match_rates = [r["match_rate"] for r in results if r.get("match_rate") is not None]
        if match_rates:
            avg_match = sum(match_rates) / len(match_rates)
            print(f"平均匹配率: {avg_match:.1f}%")

        return results


async def main():
    parser = argparse.ArgumentParser(description="租房 Agent 本地调试运行器")
    parser.add_argument(
        "--sample",
        type=str,
        help="指定单个测试样例文件路径"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试样例"
    )
    parser.add_argument(
        "--samples-dir",
        type=str,
        default="tests/test_samples",
        help="测试样例目录（默认：tests/test_samples）"
    )
    parser.add_argument(
        "--model-ip",
        type=str,
        required=True,
        help="模型服务 IP 地址"
    )
    parser.add_argument(
        "--agent-url",
        type=str,
        default="http://localhost:8191",
        help="Agent 服务地址（默认：http://localhost:8191）"
    )

    args = parser.parse_args()

    runner = DebugRunner(args.model_ip, args.agent_url)

    if args.sample:
        await runner.run_sample(args.sample)
    elif args.all:
        await runner.run_all_samples(args.samples_dir)
    else:
        print("请指定 --sample 或 --all 参数")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())