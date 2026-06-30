import { Injectable } from '@nestjs/common';
import { PrismaService, ResponseService } from '@libs/shared';

@Injectable()
export class LearnService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly response: ResponseService
  ) { }
  //读取单词列表
  async getWordList(id: string, userId: string) {
    //1.如果他没有购买过课程进入这个页面 非法请求
    const courseRecord = await this.prisma.courseRecord.findFirst({
      where: {
        userId: userId,
        courseId: id,
        isPurchased: true
      },
      include: {
        course: true
      }
    })
    if (!courseRecord) {
      return this.response.error(null, '非法请求');
    }
    const courseType = courseRecord.course.value; //gk zk
    //A B
    //点击完保存之后A->wordBookRecord 说明A学习过了
    const words = await this.prisma.wordBook.findMany({
      where: {
        [courseType]: true, //gk:true
        //掌握的单词不能被查出来
        wordBookRecords: {
          none: {
            userId: userId
          }
        }
      },
      skip: 0, //跳过0条 从第一条开始
      take: 10, //取10条
      orderBy: {
        frq: 'desc' //排序频率越高越靠前
      },
    })
    return this.response.success(words);
  }

  //保存单词到wordBookRecord
  async saveWordMaster(wordIds: string[], userId: string) {
    if (!wordIds || !Array.isArray(wordIds) || wordIds.length === 0) {
      const user = await this.prisma.user.findUnique({
        where: { id: userId },
      });
      return this.response.success({
        wordNumber: user?.wordNumber ?? 0,
      });
    }

    const uniqueWordIds = Array.from(new Set(wordIds));
    const existing = await this.prisma.wordBookRecord.findMany({
      where: { userId, wordId: { in: uniqueWordIds } },
    });
    const existingMap = new Map(existing.map(r => [r.wordId, r]));
    const unmasteredExistingIds = uniqueWordIds.filter(id => existingMap.has(id) && !existingMap.get(id)!.isMaster);
    const newWordIds = uniqueWordIds.filter(id => !existingMap.has(id));

    let userWordNumber: number;
    const totalNewlyMastered = unmasteredExistingIds.length + newWordIds.length;

    if (totalNewlyMastered > 0) {
      const updatedUser = await this.prisma.$transaction(async (tx) => {
        if (unmasteredExistingIds.length > 0) {
          await tx.wordBookRecord.updateMany({
            where: { userId, wordId: { in: unmasteredExistingIds } },
            data: { isMaster: true },
          });
        }
        if (newWordIds.length > 0) {
          await tx.wordBookRecord.createMany({
            data: newWordIds.map(id => ({ userId, wordId: id, isMaster: true })),
            skipDuplicates: true,
          });
        }
        return tx.user.update({
          where: { id: userId },
          data: { wordNumber: { increment: totalNewlyMastered } },
        });
      });
      userWordNumber = updatedUser.wordNumber;
    } else {
      const user = await this.prisma.user.findUnique({
        where: { id: userId },
      });
      userWordNumber = user?.wordNumber ?? 0;
    }

    return this.response.success({
      wordNumber: userWordNumber,
    });
  }

  //记录错题
  async recordMistake(wordId: string, userId: string) {
    if (!wordId) {
      return this.response.error(null, '非法单词请求');
    }
    const record = await this.prisma.wordBookRecord.upsert({
      where: {
        userId_wordId: {
          userId,
          wordId,
        },
      },
      update: {
        isMaster: false,
      },
      create: {
        userId,
        wordId,
        isMaster: false,
      },
    });
    return this.response.success(record);
  }

  //获取错题列表
  async getMistakeList(userId: string) {
    const records = await this.prisma.wordBookRecord.findMany({
      where: {
        userId,
        isMaster: false,
      },
      include: {
        word: true,
      },
      orderBy: {
        updatedAt: 'desc',
      },
    });
    return this.response.success(records.map(r => r.word));
  }

  //解决错题（设为已掌握）
  async resolveMistake(wordId: string, userId: string) {
    if (!wordId) {
      return this.response.error(null, '非法单词请求');
    }
    const result = await this.prisma.$transaction(async (tx) => {
      const record = await tx.wordBookRecord.findUnique({
        where: {
          userId_wordId: {
            userId,
            wordId,
          },
        },
      });
      if (!record || record.isMaster) {
        return null;
      }
      await tx.wordBookRecord.update({
        where: {
          id: record.id,
        },
        data: {
          isMaster: true,
        },
      });
      const updatedUser = await tx.user.update({
        where: { id: userId },
        data: {
          wordNumber: {
            increment: 1,
          },
        },
      });
      return updatedUser;
    });

    if (!result) {
      return this.response.error(null, '错题记录不存在或已掌握');
    }
    return this.response.success(result);
  }
}

